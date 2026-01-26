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
DEFAULT_SPECIAL_DIRS: Dict[str, Set[str]] = {
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
        "homebrew",
    },
    "IDE Config": {".idea", ".vscode", ".vs", ".eclipse", ".fleet"},
    "Git Repos": {".git"},
    "Temp Files": {"tmp", "temp", ".tmp"},
    "ML Artifacts": {"weights", "checkpoints", "pretrained"},
}


def _load_and_merge_config(
    defaults: Dict[str, Set[str]], config_key: str, replace_key: str
) -> Dict[str, Set[str]]:
    """Load and merge user configuration from ~/.zpace.toml."""
    result = {cat: items.copy() for cat, items in defaults.items()}

    if not USER_CONFIG_PATH.exists():
        return result

    if tomllib is None:
        return result

    try:
        with open(USER_CONFIG_PATH, "rb") as f:
            user_config = tomllib.load(f)
    except Exception:
        return result

    user_items = user_config.get(config_key, {})
    for cat_name, cat_config in user_items.items():
        if cat_name not in result:
            result[cat_name] = set()

        if replace_key in cat_config:
            result[cat_name] = set(cat_config[replace_key])
        if "add" in cat_config:
            result[cat_name].update(cat_config["add"])
        if "remove" in cat_config:
            result[cat_name] -= set(cat_config["remove"])

    return result


def load_user_categories_config() -> Dict[str, Set[str]]:
    """Load and merge user file category configuration from ~/.zpace.toml."""
    return _load_and_merge_config(DEFAULT_CATEGORIES, "categories", "extensions")


def load_user_dirs_config() -> Dict[str, Set[str]]:
    """Load and merge user directory configuration from ~/.zpace.toml."""
    return _load_and_merge_config(DEFAULT_SPECIAL_DIRS, "directories", "dirs")


CATEGORIES = load_user_categories_config()
SPECIAL_DIRS = load_user_dirs_config()

# Pre-compute lookups for O(1) access
EXTENSION_MAP = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}
SPECIAL_DIR_MAP = {name: cat for cat, names in SPECIAL_DIRS.items() for name in names}
PROGRESS_UPDATE_THRESHOLD = 10 * 1024 * 1024  # 10 MB
