import sys
from pathlib import Path
from typing import Dict, Set

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore[assignment]

MIN_FILE_SIZE = 100 * 1024  # 100 KB
DEFAULT_TOP_N = 10
USER_CONFIG_PATH = Path.home() / ".zpace.toml"

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

DEFAULT_CATEGORIES: Dict[str, Set[str]] = {
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
        ".ico",
        ".raw",
        ".avif",
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
        ".md",
        ".epub",
        ".mobi",
        ".pages",
        ".numbers",
        ".key",
    },
    "Music": {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg", ".wma", ".opus", ".aiff"},
    "Videos": {
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".mts",
        ".vob",
        ".3gp",
    },
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
        ".ipynb",
        ".sh",
        ".bash",
        ".zsh",
        ".ps1",
        ".swift",
        ".kt",
        ".scala",
        ".php",
        ".vue",
        ".svelte",
        ".h",
        ".hpp",
    },
    "Archives": {".tar", ".gz", ".zip", ".rar", ".7z", ".bz2", ".xz", ".tgz", ".lz", ".zst"},
    "Disk Images": {".iso", ".dmg", ".img", ".vdi", ".vmdk", ".qcow2", ".vhd", ".vhdx"},
    "Config": {".yml", ".yaml", ".json", ".toml", ".xml", ".ini", ".env", ".conf"},
    "ML Models": {
        ".pt",
        ".pth",
        ".onnx",
        ".keras",
        ".safetensors",
        ".tflite",
        ".gguf",
        ".pkl",
        ".pb",
        ".ckpt",
    },
    "Databases": {
        ".db",
        ".sqlite",
        ".sqlite3",
        ".h5",
        ".hdf5",
        ".parquet",
        ".mdb",
        ".accdb",
        ".dbf",
        ".csv",
        ".tsv",
        ".avro",
        ".duckdb",
    },
    "3D Models": {".obj", ".fbx", ".stl", ".blend", ".gltf", ".glb"},
    "Executables": {".exe", ".dll", ".so", ".dylib"},
}

# Special directories to treat as atomic units
SPECIAL_DIRS = {
    "Virtual Environments": {
        ".venv",
        "venv",
        "env",
        "virtualenv",
        ".virtualenv",
        "conda",
        ".conda",
        "miniconda3",
        "anaconda3",
    },
    "Node Modules": {"node_modules"},
    "Build Artifacts": {
        "target",
        "build",
        "dist",
        ".gradle",
        ".cargo",
        "out",
        ".next",
        ".nuxt",
        ".svelte-kit",
        ".turbo",
        ".bazel",
        "bazel-bin",
        "bazel-out",
    },
    "Package Caches": {
        ".npm",
        ".yarn",
        ".m2",
        ".pip",
        "__pycache__",
        ".cache",
        ".pnpm",
        ".uv",
        "vendor",
        ".bundle",
        ".bun",
        ".deno",
    },
    "IDE Config": {".idea", ".vscode", ".vs", ".eclipse", ".fleet"},
    "Git Repos": {".git"},
    "Temp Files": {"tmp", "temp", ".tmp"},
    "ML Artifacts": {"weights", "checkpoints", "pretrained"},
}


def load_user_config() -> Dict[str, Set[str]]:
    """Load and merge user configuration from ~/.zpace.toml if it exists."""
    categories = {cat: exts.copy() for cat, exts in DEFAULT_CATEGORIES.items()}

    if not USER_CONFIG_PATH.exists():
        return categories

    if tomllib is None:
        return categories

    try:
        with open(USER_CONFIG_PATH, "rb") as f:
            user_config = tomllib.load(f)
    except Exception:
        return categories

    user_categories = user_config.get("categories", {})
    for cat_name, cat_config in user_categories.items():
        if cat_name not in categories:
            categories[cat_name] = set()

        if "extensions" in cat_config:
            categories[cat_name] = set(cat_config["extensions"])
        if "add" in cat_config:
            categories[cat_name].update(cat_config["add"])
        if "remove" in cat_config:
            categories[cat_name] -= set(cat_config["remove"])

    return categories


CATEGORIES = load_user_config()

# Pre-compute lookups for O(1) access
EXTENSION_MAP = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}
SPECIAL_DIR_MAP = {name: cat for cat, names in SPECIAL_DIRS.items() for name in names}
PROGRESS_UPDATE_THRESHOLD = 10 * 1024 * 1024  # 10 MB
