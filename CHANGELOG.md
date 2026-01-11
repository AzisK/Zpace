# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

## [0.4.0] - 2026-01-11

### Refactoring
- **Project Structure**: Refactored the monolithic `main.py` into a modular package structure under the `zpace/` directory. This improves maintainability, separation of concerns, and scalability.
  - `zpace/main.py`: Handles CLI argument parsing and high-level orchestration.
  - `zpace/core.py`: Contains the core scanning and categorization logic.
  - `zpace/config.py`: Centralizes all configuration constants.
  - `zpace/utils.py`: Includes helper functions for size formatting and platform-specific paths.

### Documentation
- **Architecture**: Updated `ARCHITECTURE.md` to reflect the new modular project structure and data flow.
- **README**: Updated the "Project Structure" and "Development" sections in `README.md` to match the refactored code.

### Tests
- **Test Suite**: Fixed all unit and integration tests that were broken by the refactoring. Updated import paths and mock targets to align with the new package structure.

## [0.3.1] - 2026-01-10

### Features
- **CLI**: Added `--version` argument to allow users to check the installed version of the tool.

### Documentation
- Added `AGENTS.md` to define best practices for AI agent interactions with the codebase.


## [0.3.0] - 2026-01-08

### Features
- **Performance**: Refactored file scanning to use an iterative `os.scandir` approach and string-based path handling, significantly improving performance and reducing memory usage.
- **Symlink Handling**: The tool now explicitly detects and rejects symlinks as the initial scan path, preventing unexpected behavior.

### Improvements
- **CI**: Switched GitHub Actions runners to `ubuntu-slim` to optimize resource usage.

### Fixes
- **Path Resolution**: Improved path resolution in the main scanning function.
- **Trash Size Check**: Made the trash size calculation more robust.


## [0.2.0] - 2025-12-03

### Features
- **Trash Bin Size**: Added reporting of Trash bin size in the disk usage output.
- **Cross-Platform Support**: Added support for checking Trash size on macOS, Linux, and Windows.
- **Symlink Skipping**: Explicitly skip symlinks during scanning to prevent infinite loops and double counting.
- **Architecture Documentation**: Added `ARCHITECTURE.md` to document the project structure and design.

### Improvements
- **Performance**: Optimized file and directory categorization using O(1) lookups.
- **Performance**: Used `os.scandir` context manager in `calculate_dir_size` for better resource management.
- **Output**: Added zpace example output to `README.md`.
- **Documentation**: Added instructions for granting "Full Disk Access" on macOS.

### Tests
- **Comprehensive Coverage**: Added tests for output formatting (`print_results`), CLI argument parsing, symlink handling, and Unicode filenames.
- **Integration Tests**: Added integration tests for `get_trash_path` running on the actual OS.
- **Windows Support**: Improved Windows path verification in integration tests.

### CI/CD
- **AI Code Review**: Added a GitHub Action workflow to review pull requests using an LLM.
- **Trivia Workflow**: Added a fun Trivia workflow for PRs.
- **CI Improvements**: Added Windows to the CI test matrix, added `mypy` type checking, and improved test structure.

[Commits](https://github.com/AzisK/Zpace/compare/v0.1.1...v0.2.0)

## [0.1.1] - 2025-10-23

Rename executable from space to zpace since space is already taken on PyPI.

[Commits](https://github.com/AzisK/Zpace/compare/v0.1.0...v0.1.1)


## [0.1.0] - 2025-10-19

Initial commit and release of the Zpace tool.

[Commits](https://github.com/AzisK/Zpace/commits/v0.1.0)
