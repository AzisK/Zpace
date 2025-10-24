# Zpace

A CLI tool to discover what's hogging your disk space!

The tool shows the largest files in each category of files (videos, pictures, documents etc.) as well as the largest special directories as apps in MacOS, Python virtual environments, node_modules etc.

It's built to indentify the biggest chunks of data that could potentially free up the space for something else.

## Features

- 📊 Smart Categorization - Groups files by type (Documents, Videos, Code, Pictures, etc.)
- 📦 Special Directory Detection - Identifies space-hungry directories like node_modules, .venv, .git, and build artifacts
- 🎯 Actionable Insights - Shows deletable units to help you quickly free up space
- ⚡ Fast Scanning - Efficient traversal with real-time progress tracking
- 🔍 Sparse File Handling - Correctly reports actual disk usage for Docker images and other sparse files
- 🎨 Clean Output - Organized and clear display with helpful statistics

## Installation

```bash
uv tool install space
```

```bash
pip install space
```

## Usage

### Basic Commands
```bash
# Scan your home directory (default)
zpace

# Scan a specific directory
zpace /path/to/directory

# Scan current directory
zpace .
```

### Options
```bash
# Show top 20 items per category (default: 10)
zpace -n 20

# Set minimum file size to 1MB (default: 100KB)
zpace -m 1024

# Combine options
zpace ~/Documents -n 15 -m 500
```

### Tips

```bash
# Find all node_modules directories
zpace ~ -n 50 | grep "node_modules"

# Check what's in a specific directory
zpace ~/.cache

# Find largest files system-wide (requires sudo)
sudo zpace / -n 20
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/azisk/zpace.git
cd zpace

# Install dependencies
uv sync

# Run locally
uv run python main.py
```

### Code Quality

The project uses Ruff for linting, formatting, and import sorting:

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Fix auto-fixable issues
uv run ruff check --fix

# Run all pre-commit checks manually
uv run pre-commit run --all-files
```

### Testing

```bash
# Run tests
uv run pytest test_main.py -v

# Test across multiple Python versions (optional)
./testVersions.sh
```

### Project Structure
```
zpace/
├── main.py           # Main application code
├── pyproject.toml    # Project configuration
├── README.md         # This file
└── CHANGELOG.md      # Version history
```

### Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

### License
Apacha 2.0 License

### Support

- 🐛 [Report a bug](https://github.com/AzisK/Zpace/issues)
- 💡 [Request a feature](https://github.com/AzisK/Zpace/issues)
- ⭐ Star the repo if you find it useful!

---

Made with love for people tired of full disks
