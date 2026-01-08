# Zpace Architecture

## Overview
Zpace is a CLI tool designed to analyze disk usage and identify large files and directories. It categorizes files by type (e.g., Pictures, Code, Archives) and identifies "special directories" that should be treated as atomic units (e.g., `.git`, `node_modules`).

## Core Logic

### 1. File Categorization
Files are categorized based on their extensions. The `CATEGORIES` dictionary in `main.py` defines these mappings.
- **Categories**: Pictures, Documents, Music, Videos, Code, Archives, Disk Images, JSON/YAML.
- **Fallback**: Any file not matching a known extension is categorized as "Others".

### 2. Special Directory Detection
Certain directories are treated as single units rather than traversing their contents. This is done for directories where the files are meant to stay together to support the logic. These directories might not have very big files inside but they might have lots of them. This way we can detect the size of build and target directories, virtual environment, MacOS apps, node modules direcories etc.

- **Logic**: `identify_special_dir` checks if a directory name matches a set of known names (defined in `SPECIAL_DIRS`) or if it is a macOS `.app` bundle.
- **Examples**: `node_modules`, `.venv`, `.git`, `target`, `.idea`.

### 3. Scanning Algorithm
The tool uses an iterative, stack-based, depth-first search approach with `os.scandir`. This is more performant than the previous `os.walk` implementation as it avoids the overhead of `os.walk` and creating `pathlib.Path` objects in performance-critical sections.
- **Optimization**: System directories (e.g., `/proc`, `/sys`, `/System`) are skipped to improve performance and avoid permission errors.
- **Progress Tracking**: A `tqdm` progress bar shows real-time scanning progress based on bytes processed.

## Key Functions

- **`scan_files_and_dirs(root_path, used_bytes, min_size)`**: The main driver function. It uses an iterative, stack-based approach with `os.scandir` to traverse the directory tree, handles special directories, and aggregates file/directory statistics.
- **`categorize_extension(extension)`**: Determines the category of a file based on its extension.
- **`identify_special_dir_name(dirname)`**: Checks if a directory is a "special" directory.
- **`calculate_dir_size_recursive(dirpath)`**: Recursively calculates the size of a directory. Used for "special directories" where we don't want to categorize individual files inside.

## Configuration

Configuration is primarily handled via global constants in `main.py`:
- `SKIP_DIRS`: Set of system paths to ignore.
- `CATEGORIES`: Mapping of category names to file extensions.
- `SPECIAL_DIRS`: Mapping of category names to directory names.
- `MIN_FILE_SIZE`: Threshold for tracking individual files (default 100KB).

Other configuration is done via the arguments of CLI.

```bash
python main.py <path> --min-size <size> --top-n <n>
```

- `<path>`: Path to scan (default: current directory)
- `<size>`: Min size of files to categorize (default: 100KB)
- `<n>`: Number of top files to display from each category (default: 10)
