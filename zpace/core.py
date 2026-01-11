import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm

from zpace.config import (
    DEEPEST_SKIP_LEVEL,
    EXTENSION_MAP,
    MIN_FILE_SIZE,
    PROGRESS_UPDATE_THRESHOLD,
    SKIP_DIRS,
    SPECIAL_DIR_MAP,
    DEFAULT_TOP_N,
)


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
