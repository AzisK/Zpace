import argparse
import importlib.metadata
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import sys
from tqdm import tqdm

MIN_FILE_SIZE = 100 * 1024  # 100 KB
DEFAULT_TOP_N = 10

# Use strings for faster lookups (avoiding Path object creation overhead during checks)
SKIP_DIRS: Set[str] = {
    # Linux
    "/dev",
    "/proc",
    "/sys",
    "/run",
    "/var/run",
    "/snap",
    "/boot",
    "/lost+found",
    # macOS
    "/System",
    "/Library",
    "/private/var",
    "/.Spotlight-V100",
    "/.DocumentRevisions-V100",
    "/.fseventsd",
}

DEEPEST_SKIP_LEVEL = 3

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

# Pre-compute lookups for O(1) access
EXTENSION_MAP = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}
SPECIAL_DIR_MAP = {name: cat for cat, names in SPECIAL_DIRS.items() for name in names}
PROGRESS_UPDATE_THRESHOLD = 10 * 1024 * 1024  # 10 MB


def get_disk_usage(path: str):
    total, used, free = shutil.disk_usage(path)
    return total, used, free


def categorize_extension(extension: str) -> str:
    """Extension should include the dot, e.g. '.py'"""
    return EXTENSION_MAP.get(extension.lower(), "Others")


def is_skip_path(dirpath: str) -> bool:
    """Check if directory path should be skipped (system directories)."""
    return dirpath in SKIP_DIRS


def identify_special_dir_name(dirname: str) -> Optional[str]:
    """
    Check if directory name indicates a special directory.
    """
    # Check for macOS .app bundles
    if dirname.endswith(".app"):
        return "macOS Apps"

    return SPECIAL_DIR_MAP.get(dirname.lower())


def calculate_dir_size_recursive(dirpath: str) -> int:
    """
    Calculate total size of directory using os.scandir recursively.
    """
    total_size = 0
    try:
        with os.scandir(dirpath) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        stat = entry.stat(follow_symlinks=False)
                        # st_blocks is 512-byte blocks. reliable on unix.
                        # fallback to st_size if not available (e.g. windows sometimes)
                        total_size += (
                            stat.st_blocks * 512 if hasattr(stat, "st_blocks") else stat.st_size
                        )
                    elif entry.is_dir(follow_symlinks=False):
                        total_size += calculate_dir_size_recursive(entry.path)
                except (FileNotFoundError, PermissionError, OSError):
                    continue
    except (FileNotFoundError, PermissionError, OSError):
        pass

    return total_size


def scan_files_and_dirs(
    root_path: Path, used_bytes: int, min_size: int = MIN_FILE_SIZE
) -> Tuple[Dict[str, List[Tuple[int, str]]], Dict[str, List[Tuple[int, str]]], int, int]:
    """
    Scan directory tree for files and special directories using an iterative stack with os.scandir.
    Returns: (file_categories, dir_categories, total_files, total_size)
    """
    file_categories = defaultdict(list)
    dir_categories = defaultdict(list)
    scanned_files = 0
    scanned_size = 0
    progress_update_buffer = 0

    # Stack for iterative traversal: (path_string, level)
    start_level = len(root_path.parts)
    stack = [(str(root_path), start_level)]

    # Pre-compute root level usage to skip logic if needed
    # We'll just check absolute paths for SKIP_DIRS

    with tqdm(total=used_bytes, unit="B", unit_scale=True, desc="Scanning") as pbar:
        while stack:
            current_path, level = stack.pop()

            try:
                # Use os.scandir which is much faster than os.walk + os.stat
                # and avoids creating Path objects for every iteration
                with os.scandir(current_path) as it:
                    dirs_to_visit = []

                    for entry in it:
                        try:
                            # 1. Handle Directories
                            if entry.is_dir(follow_symlinks=False):
                                dirname = entry.name
                                entry_path = entry.path

                                # Check global skip dirs (usually top level system dirs)
                                # Only check if we are shallow enough to be a skip dir
                                if level <= DEEPEST_SKIP_LEVEL and is_skip_path(entry_path):
                                    continue

                                # Check special directories
                                special_type = identify_special_dir_name(dirname)
                                if special_type:
                                    # Calculate size as atomic unit
                                    dir_size = calculate_dir_size_recursive(entry_path)

                                    if dir_size >= min_size:
                                        # Storing string path instead of Path object
                                        dir_categories[special_type].append((dir_size, entry_path))

                                    scanned_size += dir_size
                                    progress_update_buffer += dir_size
                                    continue  # Do not descend into special dirs

                                # If normal directory, schedule for visit
                                dirs_to_visit.append((entry_path, level + 1))

                            # 2. Handle Files
                            elif entry.is_file(follow_symlinks=False):
                                stat = entry.stat(follow_symlinks=False)
                                size = (
                                    stat.st_blocks * 512
                                    if hasattr(stat, "st_blocks")
                                    else stat.st_size
                                )

                                if size >= min_size:
                                    _, ext = os.path.splitext(entry.name)
                                    category = categorize_extension(ext)
                                    file_categories[category].append((size, entry.path))

                                scanned_files += 1
                                scanned_size += size
                                progress_update_buffer += size

                        except (FileNotFoundError, PermissionError, OSError):
                            continue

                    for d in dirs_to_visit:
                        stack.append(d)

                    # Update progress bar
                    if progress_update_buffer >= PROGRESS_UPDATE_THRESHOLD:
                        pbar.update(progress_update_buffer)
                        progress_update_buffer = 0

            except (FileNotFoundError, PermissionError, OSError):
                continue

        # Final progress update
        if progress_update_buffer > 0:
            pbar.update(progress_update_buffer)

    return dict(file_categories), dict(dir_categories), scanned_files, scanned_size


def get_top_n_per_category(
    categorized: Dict[str, List[Tuple[int, str]]], top_n: int = DEFAULT_TOP_N
) -> Dict[str, List[Tuple[int, str]]]:
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


def get_trash_path() -> Optional[str]:
    """Get the path to the Trash/Recycle Bin based on the OS."""
    if sys.platform == "darwin":
        return str(Path.home() / ".Trash")
    elif sys.platform == "linux":
        return str(Path.home() / ".local" / "share" / "Trash")
    elif sys.platform == "win32":
        system_drive = os.environ.get("SystemDrive", "C:")
        return str(Path(system_drive) / "$Recycle.Bin")
    return None


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
                    trash_size = calculate_dir_size_recursive(trash_path)
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


if __name__ == "__main__":
    import time

    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"Scan completed in {elapsed:.2f}s")
