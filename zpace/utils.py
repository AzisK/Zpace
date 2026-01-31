import os
import shutil
import sys
from pathlib import Path
from typing import Optional


def get_disk_usage(path: str):
    try:
        total, used, free = shutil.disk_usage(path)
        return total, used, free
    except (AttributeError, OSError):
        return 0, 0, 0


def format_size(size: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


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
