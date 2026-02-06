import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DiskUsage:
    total_bytes: int
    used_bytes: int
    free_bytes: int
    used_percent: float
    trash_bytes: Optional[int] = None


@dataclass
class FileEntry:
    path: str
    size_bytes: int


@dataclass
class ScanSummary:
    total_files: int
    special_directories_count: int
    total_size_bytes: int


@dataclass
class ScanResult:
    version: str = "1.0"
    scan_path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    disk_usage: Optional[DiskUsage] = None
    scan_summary: Optional[ScanSummary] = None
    special_directories: Dict[str, List[FileEntry]] = field(default_factory=dict)
    files_by_category: Dict[str, List[FileEntry]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "version": self.version,
            "scan_path": self.scan_path,
            "timestamp": self.timestamp,
        }

        if self.disk_usage:
            result["disk_usage"] = {
                "total_bytes": self.disk_usage.total_bytes,
                "used_bytes": self.disk_usage.used_bytes,
                "free_bytes": self.disk_usage.free_bytes,
                "used_percent": self.disk_usage.used_percent,
            }
            if self.disk_usage.trash_bytes is not None:
                result["disk_usage"]["trash_bytes"] = self.disk_usage.trash_bytes

        if self.scan_summary:
            result["scan_summary"] = {
                "total_files": self.scan_summary.total_files,
                "special_directories_count": self.scan_summary.special_directories_count,
                "total_size_bytes": self.scan_summary.total_size_bytes,
            }

        result["special_directories"] = {
            category: [{"path": e.path, "size_bytes": e.size_bytes} for e in entries]
            for category, entries in sorted(self.special_directories.items())
        }

        result["files_by_category"] = {
            category: [{"path": e.path, "size_bytes": e.size_bytes} for e in entries]
            for category, entries in sorted(self.files_by_category.items())
        }

        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def build_scan_result(
    scan_path: str,
    total: float,
    used: float,
    free: float,
    trash_size: Optional[int],
    file_categories: Dict[str, List[tuple]],
    dir_categories: Dict[str, List[tuple]],
    total_files: int,
    total_size: int,
) -> ScanResult:
    """Build a ScanResult from raw scan data."""
    used_percent = (used / total * 100) if total > 0 else 0.0

    disk_usage = DiskUsage(
        total_bytes=int(total),
        used_bytes=int(used),
        free_bytes=int(free),
        used_percent=round(used_percent, 1),
        trash_bytes=trash_size,
    )

    # Count special directories
    special_dirs_count = sum(len(entries) for entries in dir_categories.values())

    scan_summary = ScanSummary(
        total_files=total_files,
        special_directories_count=special_dirs_count,
        total_size_bytes=total_size,
    )

    # Convert tuples to FileEntry objects
    special_directories = {
        category: [FileEntry(path=path, size_bytes=size) for size, path in entries]
        for category, entries in dir_categories.items()
    }

    files_by_category = {
        category: [FileEntry(path=path, size_bytes=size) for size, path in entries]
        for category, entries in file_categories.items()
    }

    return ScanResult(
        scan_path=scan_path,
        disk_usage=disk_usage,
        scan_summary=scan_summary,
        special_directories=special_directories,
        files_by_category=files_by_category,
    )
