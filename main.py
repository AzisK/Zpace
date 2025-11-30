import argparse
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
from tqdm import tqdm

MIN_FILE_SIZE = 100 * 1024  # 100 KB
DEFAULT_TOP_N = 10

# Use Path objects for cross-platform compatibility
SKIP_DIRS = {
    # Linux
    Path("/dev"),
    Path("/proc"),
    Path("/sys"),
    Path("/run"),
    Path("/var/run"),
    Path("/snap"),
    Path("/boot"),
    Path("/lost+found"),
    # macOS
    Path("/System"),
    Path("/Library"),
    Path("/private/var"),
    Path("/.Spotlight-V100"),
    Path("/.DocumentRevisions-V100"),
    Path("/.fseventsd"),
}
# Calculate deepest level for optimization
DEEPEST_SKIP_DIRS_LEVEL = max(len(p.parts) for p in SKIP_DIRS)

CATEGORIES = {
    "Pictures": {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".svg",
        ".webp",
        ".heic",
    },
    "Documents": {
        ".doc",
        ".docx",
        ".pdf",
        ".txt",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".rtf",
    },
    "Music": {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg", ".wma"},
    "Videos": {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"},
    "Code": {
        ".py",
        ".js",
        ".html",
        ".css",
        ".java",
        ".cpp",
        ".c",
        ".rb",
        ".go",
        ".rs",
        ".ts",
        ".jsx",
        ".tsx",
    },
    "Archives": {".tar", ".gz", ".zip", ".rar", ".7z", ".bz2", ".xz"},
    "Disk Images": {".iso", ".dmg", ".img", ".vdi", ".vmdk"},
    "JSON/YAML": {".yml", ".yaml", ".json"},
}

# Special directories to treat as atomic units
SPECIAL_DIRS = {
    "Virtual Environments": {".venv", "venv", "env", "virtualenv", ".virtualenv"},
    "Node Modules": {"node_modules"},
    "Bun Modules": {".bun"},
    "Build Artifacts": {"target", "build", "dist", ".gradle", ".cargo", "out"},
    "Package Caches": {".npm", ".yarn", ".m2", ".pip", "__pycache__", ".cache"},
    "IDE Config": {".idea", ".vscode", ".vs", ".eclipse"},
    "Git Repos": {".git"},
}

# Pre-compute reverse lookups for O(1) access
EXTENSION_MAP = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}
SPECIAL_DIR_MAP = {name: cat for cat, names in SPECIAL_DIRS.items() for name in names}
PROGRESS_UPDATE_THRESHOLD = 10 * 1024 * 1024  # 10 MB


def get_disk_usage(path):
    total, used, free = shutil.disk_usage(path)
    return total, used, free


def categorize_file(filepath: Path) -> str:
    return EXTENSION_MAP.get(filepath.suffix.lower(), "Others")


def is_skip_directory(dirpath: Path) -> bool:
    """Check if directory should be skipped (system directories)."""
    return dirpath in SKIP_DIRS


def identify_special_dir(dirpath: Path) -> Optional[str]:
    """
    Check if directory is a special type that should be treated as atomic unit.
    Returns category name if special, None otherwise.
    """
    # Check for macOS .app bundles
    if dirpath.suffix == ".app":
        return "macOS Apps"

    return SPECIAL_DIR_MAP.get(dirpath.name.lower())


def calculate_dir_size(dirpath: Path) -> int:
    """
    Calculate total size of directory using os.scandir (efficient and portable).
    """
    total_size = 0
    try:
        with os.scandir(dirpath) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        stat = entry.stat(follow_symlinks=False)
                        total_size += (
                            stat.st_blocks * 512 if hasattr(stat, "st_blocks") else stat.st_size
                        )
                    elif entry.is_dir(follow_symlinks=False):
                        # Only create Path object for recursion
                        total_size += calculate_dir_size(Path(entry.path))

                except (FileNotFoundError, PermissionError, OSError):
                    continue
    except (FileNotFoundError, PermissionError, OSError):
        pass

    return total_size


def scan_files_and_dirs(
    path: Path, used: int, min_size: int = MIN_FILE_SIZE
) -> Tuple[Dict[str, List[Tuple[int, Path]]], Dict[str, List[Tuple[int, Path]]], int, int]:
    """
    Scan directory tree for files and special directories.
    Returns: (file_categories, dir_categories, total_files, total_size)
    """
    file_categories = defaultdict(list)
    dir_categories = defaultdict(list)
    scanned_files = 0
    scanned_size = 0
    progress_update_buffer = 0

    starting_level = len(path.parts)
    is_skip_dirs = True if starting_level < DEEPEST_SKIP_DIRS_LEVEL else False

    with tqdm(total=used, unit="B", unit_scale=True, desc="Scanning") as pbar:
        for root, dirs, files in os.walk(path, topdown=True):
            root_path = Path(root)

            # Check subdirectories and handle special ones BEFORE descending
            dirs_to_remove = []
            for dirname in dirs:
                dir_path = root_path / dirname

                # Skip system directories (only check if we're not too deep)
                if (
                    is_skip_dirs
                    and len(dir_path.parts) <= DEEPEST_SKIP_DIRS_LEVEL
                    and is_skip_directory(dir_path)
                ):
                    dirs_to_remove.append(dirname)
                    continue

                # Check if this subdirectory is special
                special_type = identify_special_dir(dir_path)
                if special_type:
                    # Measure it as atomic unit
                    dir_size = calculate_dir_size(dir_path)
                    if dir_size >= min_size:
                        dir_categories[special_type].append((dir_size, dir_path))
                    scanned_size += dir_size
                    progress_update_buffer += dir_size
                    # Don't descend into it
                    dirs_to_remove.append(dirname)

            # Remove directories we don't want to descend into
            for dirname in dirs_to_remove:
                dirs.remove(dirname)

            # Process files in current directory
            for name in files:
                filepath = root_path / name
                # Skip symlinks to prevent double counting and loops
                if filepath.is_symlink():
                    continue

                try:
                    stat = os.stat(filepath)
                    size = stat.st_blocks * 512 if hasattr(stat, "st_blocks") else stat.st_size

                    if size >= min_size:
                        category = categorize_file(filepath)
                        file_categories[category].append((size, filepath))

                    scanned_files += 1
                    scanned_size += size
                    progress_update_buffer += size

                    # Update progress bar every 10MB to balance performance and accuracy
                    if progress_update_buffer >= PROGRESS_UPDATE_THRESHOLD:
                        pbar.update(progress_update_buffer)
                        progress_update_buffer = 0

                except (FileNotFoundError, PermissionError, OSError):
                    continue

        # Update any remaining progress
        if progress_update_buffer > 0:
            pbar.update(progress_update_buffer)

    return dict(file_categories), dict(dir_categories), scanned_files, scanned_size


def get_top_n_per_category(
    categorized: Dict[str, List[Tuple[int, Path]]], top_n: int = DEFAULT_TOP_N
) -> Dict[str, List[Tuple[int, Path]]]:
    result = {}
    for category, entries in categorized.items():
        sorted_entries = sorted(entries, key=lambda x: x[0], reverse=True)
        result[category] = sorted_entries[:top_n]
    return result


def format_size(size: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def print_results(
    file_categories: Dict[str, List[Tuple[int, Path]]],
    dir_categories: Dict[str, List[Tuple[int, Path]]],
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


def get_trash_path() -> Optional[Path]:
    """Get the path to the Trash/Recycle Bin based on the OS."""
    if sys.platform == "darwin":
        return Path.home() / ".Trash"
    elif sys.platform == "linux":
        return Path.home() / ".local" / "share" / "Trash"
    elif sys.platform == "win32":
        system_drive = os.environ.get("SystemDrive", "C:")
        return Path(f"{system_drive}/$Recycle.Bin")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Analyze disk usage and find largest files and directories by category"
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
    scan_path = Path(args.path).expanduser().resolve()

    if not scan_path.exists():
        print(f"ERROR: Path '{scan_path}' does not exist")
        return

    if not scan_path.is_dir():
        print(f"ERROR: Path '{scan_path}' is not a directory")
        sys.exit(1)

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
        if trash_path.exists():
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


if __name__ == "__main__":
    import time

    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"Scan completed in {elapsed:.2f}s")
