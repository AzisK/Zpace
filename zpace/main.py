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
    get_top_n_per_category,
)


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

    # Display disk usage
    total, used, free = map(float, get_disk_usage(str(scan_path)))
    terminal_width = shutil.get_terminal_size().columns

    print("\nDISK USAGE")
    print("=" * terminal_width)
    print(f"  Free:  {format_size(free)} / {format_size(total)}")
    print(f"  Used:  {format_size(used)} ({used / total * 100:.1f}%)")

    # Check Trash size
    trash_path = get_trash_path()
    if trash_path:
        if os.path.exists(trash_path):
            if os.access(trash_path, os.R_OK):
                try:
                    # Verify we can actually list it (os.access might lie on some systems/containers)
                    next(os.scandir(trash_path), None)
                    trash_size = calculate_dir_size(trash_path)
                    additional_message = ""
                    if trash_size > 1000 * 1024 * 1024:  # 1000 MB
                        additional_message = " (Consider cleanin up your trash bin!)"
                    print(f"  Trash: {format_size(trash_size)}{additional_message}")
                except PermissionError:
                    print("  Trash: Access Denied")
            else:
                print("  Trash: Access Denied")
        else:
            print("  Trash: Not Found")
    else:
        print("  Trash: Unknown OS")

    print("=" * terminal_width)
    print(f"\nSCANNING: {scan_path}")
    print(f"   Min size: {args.min_size} KB")
    print()

    # Check for symlink explicitly
    if raw_path.is_symlink():
        resolved = raw_path.resolve()
        print(f"Attention - you provided a symlink: {raw_path}")
        print(f"It points to this directory: {resolved}")
        print(f"If you wish to analyse the symlinked directory, please pass its path: {resolved}")
        return

    # Scan files and directories
    try:
        file_cats, dir_cats, total_files, total_size = scan_files_and_dirs(
            scan_path, used, args.min_size * 1024
        )
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during scan: {e}")
        sys.exit(1)

    # Get top N for each category
    top_files = get_top_n_per_category(file_cats, top_n=args.top)
    top_dirs = get_top_n_per_category(dir_cats, top_n=args.top)

    # Display results
    print("\nSCAN COMPLETE!")
    print(f"   Found {total_files:,} files")
    print(f"   Found {sum(len(e) for e in dir_cats.values())} special directories")
    print(f"   Total size: {format_size(total_size)}")

    print_results(top_files, top_dirs, terminal_width)
    print("=" * terminal_width)
