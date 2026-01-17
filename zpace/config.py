from typing import Set

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

# SKIP_DIRS contains only root-level system paths (e.g., /dev, /proc, /System).
# We only check against SKIP_DIRS when level <= DEEPEST_SKIP_LEVEL as an optimization:
# deeper scans (e.g., /home/user/project) can never encounter these paths.
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
