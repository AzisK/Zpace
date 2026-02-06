import argparse
import importlib.metadata
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import sys

from zpace.config import (
    MIN_FILE_SIZE,
    DEFAULT_TOP_N,
)
from zpace.utils import get_disk_usage, format_size, get_trash_path
from zpace.core import (
    calculate_dir_size,
    scan_files_and_dirs,
)
from zpace.output import build_scan_result


def print_results(
    file_categories: Dict[str, List[Tuple[int, str]]],
    dir_categories: Dict[str, List[Tuple[int, str]]],
    terminal_width: int,
):
    """Print both file and directory results."""

    # Print special directories first
    if dir_categories:
        print(f"\n{'=' * terminal_width}")
        print("SPECIAL DIRECTORIES")
        print("=" * terminal_width)

        for category in sorted(dir_categories.keys()):
            entries = dir_categories[category]
            if not entries:
                continue

            print(f"\n{'-' * terminal_width}")
            print(f"{category} ({len(entries)} directories)")
            print("-" * terminal_width)

            for size, dirpath in entries:
                print(f"  {format_size(size):>12}  {dirpath}")

    # Print file categories
    if file_categories:
        print(f"\n{'=' * terminal_width}")
        print("LARGEST FILES BY CATEGORY")
        print("=" * terminal_width)

        for category in sorted(file_categories.keys()):
            entries = file_categories[category]
            if not entries:
                continue

            print(f"\n{'-' * terminal_width}")
            print(f"{category} ({len(entries)} files)")
            print("-" * terminal_width)

            for size, filepath in entries:
                print(f"  {format_size(size):>12}  {filepath}")


def main():
    try:
        __version__ = importlib.metadata.version("zpace")
    except importlib.metadata.PackageNotFoundError:
        __version__ = "0.0.0-dev"

    parser = argparse.ArgumentParser(
        description="Analyze disk usage and find largest files and directories by category"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(Path.home()),
        help="Path to scan (default: home directory)",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"Number of top items per category (default: {DEFAULT_TOP_N})",
    )
    parser.add_argument(
        "-m",
        "--min-size",
        type=int,
        default=MIN_FILE_SIZE // 1024,
        help=f"Minimum file/dir size in KB (default: {MIN_FILE_SIZE // 1024})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Write results to FILE instead of stdout",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )

    args = parser.parse_args()
    # Do not resolve yet, check if it's a symlink first
    raw_path = Path(args.path).expanduser()

    if not raw_path.exists():
        print(f"ERROR: Path '{raw_path}' does not exist")
        return

    if not raw_path.is_dir():
        print(f"ERROR: Path '{raw_path}' is not a directory")
        sys.exit(1)

    scan_path = raw_path.resolve()

    # Determine output mode
    quiet_mode = args.json or args.output

    # Display disk usage
    total, used, free = map(float, get_disk_usage(str(scan_path)))
    terminal_width = shutil.get_terminal_size().columns

    if not quiet_mode:
        print("\nDISK USAGE")
        print("=" * terminal_width)
        if total > 0:
            print(f"  Free:  {format_size(free)} / {format_size(total)}")
            print(f"  Used:  {format_size(used)} ({used / total * 100:.1f}%)")
        else:
            print("  (disk usage unavailable on this platform)")

    # Check Trash size
    trash_size = None
    trash_path = get_trash_path()
    if trash_path:
        if os.path.exists(trash_path):
            if os.access(trash_path, os.R_OK):
                try:
                    # Verify we can actually list it (os.access might lie on some systems/containers)
                    next(os.scandir(trash_path), None)
                    trash_size = calculate_dir_size(trash_path)
                    if not quiet_mode:
                        additional_message = ""
                        if trash_size > 1000 * 1024 * 1024:  # 1000 MB
                            additional_message = " (Consider cleaning up your trash bin!)"
                        print(f"  Trash: {format_size(trash_size)}{additional_message}")
                except PermissionError:
                    if not quiet_mode:
                        print("  Trash: Access Denied")
            else:
                if not quiet_mode:
                    print("  Trash: Access Denied")
        else:
            if not quiet_mode:
                print("  Trash: Not Found")
    else:
        if not quiet_mode:
            print("  Trash: Unknown OS")

    if not quiet_mode:
        print("=" * terminal_width)
        print(f"\nSCANNING: {scan_path}")
        print(f"   Min size: {args.min_size} KB")
        print()

    # Check for symlink explicitly
    if raw_path.is_symlink():
        resolved = raw_path.resolve()
        msg = (
            f"Attention - you provided a symlink: {raw_path}\n"
            f"It points to this directory: {resolved}\n"
            f"If you wish to analyse the symlinked directory, please pass its path: {resolved}"
        )
        if args.json:
            print(f'{{"error": "{msg}"}}')
        else:
            print(msg)
        return

    try:
        top_files, top_dirs, total_files, total_size = scan_files_and_dirs(
            scan_path, used, args.min_size * 1024, top_n=args.top, show_progress=not quiet_mode
        )
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during scan: {e}")
        sys.exit(1)

    # JSON output mode
    if args.json:
        result = build_scan_result(
            scan_path=str(scan_path),
            total=total,
            used=used,
            free=free,
            trash_size=trash_size,
            file_categories=top_files,
            dir_categories=top_dirs,
            total_files=total_files,
            total_size=total_size,
        )
        json_output = result.to_json()
        if args.output:
            with open(args.output, "w") as f:
                f.write(json_output)
                f.write("\n")
        else:
            print(json_output)
        return

    # Text file output mode (no colors, no progress - already handled)
    if args.output:
        import io

        buffer = io.StringIO()
        buffer.write("DISK USAGE\n")
        buffer.write("=" * 80 + "\n")
        buffer.write(f"  Free:  {format_size(free)} / {format_size(total)}\n")
        buffer.write(f"  Used:  {format_size(used)} ({used / total * 100:.1f}%)\n")
        if trash_size is not None:
            buffer.write(f"  Trash: {format_size(trash_size)}\n")
        buffer.write("=" * 80 + "\n\n")
        buffer.write(f"SCAN PATH: {scan_path}\n")
        buffer.write(f"Min size: {args.min_size} KB\n\n")
        buffer.write("SCAN COMPLETE!\n")
        buffer.write(f"   Found {total_files:,} files\n")
        buffer.write(f"   Found {sum(len(e) for e in top_dirs.values())} special directories\n")
        buffer.write(f"   Total size: {format_size(total_size)}\n")

        # Write special directories
        if top_dirs:
            buffer.write("\n" + "=" * 80 + "\n")
            buffer.write("SPECIAL DIRECTORIES\n")
            buffer.write("=" * 80 + "\n")
            for category in sorted(top_dirs.keys()):
                entries = top_dirs[category]
                if not entries:
                    continue
                buffer.write("\n" + "-" * 80 + "\n")
                buffer.write(f"{category} ({len(entries)} directories)\n")
                buffer.write("-" * 80 + "\n")
                for size, dirpath in entries:
                    buffer.write(f"  {format_size(size):>12}  {dirpath}\n")

        # Write file categories
        if top_files:
            buffer.write("\n" + "=" * 80 + "\n")
            buffer.write("LARGEST FILES BY CATEGORY\n")
            buffer.write("=" * 80 + "\n")
            for category in sorted(top_files.keys()):
                entries = top_files[category]
                if not entries:
                    continue
                buffer.write("\n" + "-" * 80 + "\n")
                buffer.write(f"{category} ({len(entries)} files)\n")
                buffer.write("-" * 80 + "\n")
                for size, filepath in entries:
                    buffer.write(f"  {format_size(size):>12}  {filepath}\n")

        buffer.write("=" * 80 + "\n")

        with open(args.output, "w") as f:
            f.write(buffer.getvalue())
        return

    # Display results (normal interactive mode)
    print("\nSCAN COMPLETE!")
    print(f"   Found {total_files:,} files")
    print(f"   Found {sum(len(e) for e in top_dirs.values())} special directories")
    print(f"   Total size: {format_size(total_size)}")

    print_results(top_files, top_dirs, terminal_width)
    print("=" * terminal_width)
