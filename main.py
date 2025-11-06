import argparse
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm

MIN_FILE_SIZE = 100 * 1024  # 100 KB
DEFAULT_TOP_N = 10
SKIP_DIRS = {
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
DEEPEST_SKIP_DIRS_LEVEL = max(dirpath.count("/") for dirpath in SKIP_DIRS)
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
PROGRESS_UPDATE_THRESHOLD = 10 * 1024 * 1024  # 10 MB


def get_disk_usage(path):
    total, used, free = shutil.disk_usage(path)
    return total, used, free


def categorize_file(filepath: str) -> str:
    suffix = "." + filepath.split(".")[-1].lower()

    for category, extensions in CATEGORIES.items():
        if suffix in extensions:
            return category

    return "Others"


def should_skip_directory(dirpath: str) -> bool:
    return dirpath in SKIP_DIRS


def identify_special_dir(dirpath: str) -> Optional[str]:
    """
    Check if directory is a special type that should be treated as atomic unit.
    Returns category name if special, None otherwise.
    """
    dir_name = dirpath.split("/")[-1].lower()

    # Check for macOS .app bundles
    if dirpath.endswith(".app"):
        return "macOS Apps"

    # Check special directory names
    for category, names in SPECIAL_DIRS.items():
        if dir_name in names:
            return category

    return None


def calculate_dir_size(dirpath: str) -> int:
    """
    Calculate total size of directory using os.scandir (efficient and portable).
    """
    total_size = 0
    try:
        for entry in os.scandir(dirpath):
            try:
                if entry.is_file(follow_symlinks=False):
                    stat = entry.stat(follow_symlinks=False)
                    total_size += (
                        stat.st_blocks * 512 if hasattr(stat, "st_blocks") else stat.st_size
                    )
                elif entry.is_dir(follow_symlinks=False):
                    total_size += calculate_dir_size(entry.path)

            except (FileNotFoundError, PermissionError, OSError):
                continue
    except (FileNotFoundError, PermissionError, OSError):
        pass

    return total_size


def scan_files_and_dirs(
    path: Path, used: int, min_size: int = MIN_FILE_SIZE
) -> Tuple[Dict[str, List[Tuple[int, str]]], Dict[str, List[Tuple[int, str]]], int, int]:
    """
    Scan directory tree for files and special directories.
    Returns: (file_categories, dir_categories, total_files, total_size)
    """
    file_categories = defaultdict(list)
    dir_categories = defaultdict(list)
    scanned_files = 0
    scanned_size = 0
    progress_update_buffer = 0

    with tqdm(total=used, unit="B", unit_scale=True, desc="Scanning") as pbar:
        for level, (root, dirs, files) in enumerate(os.walk(path, topdown=True)):
            if level == 0:
                root = root.rstrip("/")
                starting_level = root.count("/")

            # Check subdirectories and handle special ones BEFORE descending
            dirs_to_remove = []
            for dirname in dirs:
                dir_path = f"{root}/{dirname}"

                # Skip system directories
                if starting_level < DEEPEST_SKIP_DIRS_LEVEL:
                    if should_skip_directory(dir_path):
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
                filepath = f"{root}/{name}"
                try:
                    stat = os.stat(filepath)
                    size = stat.st_blocks * 512 if hasattr(stat, "st_blocks") else stat.st_size

                    if size >= min_size:
                        category = categorize_file(name)
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
        print(f"\n{'═' * terminal_width}")
        print("📦 SPECIAL DIRECTORIES")
        print("═" * terminal_width)

        for category in sorted(dir_categories.keys()):
            entries = dir_categories[category]
            if not entries:
                continue

            print(f"\n{'─' * terminal_width}")
            print(f"📁 {category} ({len(entries)} directories)")
            print("─" * terminal_width)

            for size, dirpath in entries:
                print(f"  {format_size(size):>12}  {dirpath}")

    # Print file categories
    if file_categories:
        print(f"\n{'═' * terminal_width}")
        print("📄 LARGEST FILES BY CATEGORY")
        print("═" * terminal_width)

        for category in sorted(file_categories.keys()):
            entries = file_categories[category]
            if not entries:
                continue

            print(f"\n{'─' * terminal_width}")
            print(f"📁 {category} ({len(entries)} files)")
            print("─" * terminal_width)

            for size, filepath in entries:
                print(f"  {format_size(size):>12}  {filepath}")


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
        print(f"❌ Error: Path '{scan_path}' does not exist")
        return

    # Display disk usage
    total, used, free = map(float, get_disk_usage(str(scan_path)))
    terminal_width = shutil.get_terminal_size().columns

    print("\n💾 Disk Usage")
    print("═" * terminal_width)
    print(f"  Free:  {format_size(free)} / {format_size(total)}")
    print(f"  Used:  {format_size(used)} ({used / total * 100:.1f}%)")
    print("═" * terminal_width)
    print(f"\n🔍 Scanning: {scan_path}")
    print(f"   Min size: {args.min_size} KB")
    print()

    # Scan files and directories
    file_cats, dir_cats, total_files, total_size = scan_files_and_dirs(
        scan_path, used, args.min_size * 1024
    )

    # Get top N for each category
    top_files = get_top_n_per_category(file_cats, top_n=args.top)
    top_dirs = get_top_n_per_category(dir_cats, top_n=args.top)

    # Display results
    print("\n✅ Scan complete!")
    print(f"   Found {total_files:,} files")
    print(f"   Found {sum(len(e) for e in dir_cats.values())} special directories")
    print(f"   Total size: {format_size(total_size)}")

    print_results(top_files, top_dirs, terminal_width)


if __name__ == "__main__":
    import time

    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"⏱️  Scan completed in {elapsed:.2f}s")
