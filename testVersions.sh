#!/bin/bash
# Quick local test script for multiple Python versions
# For CI/CD, use GitHub Actions instead

set -e

VERSIONS=("3.9" "3.10" "3.11" "3.12" "3.13" "3.14")

echo "🧪 Testing Space across Python versions..."
echo "💡 Note: For full CI, push to GitHub (uses Actions)"
echo ""

# Run pre-commit checks first
echo "Running pre-commit checks..."
uv run pre-commit run --all-files || {
    echo "❌ Pre-commit checks failed. Fix issues and try again."
    exit 1
}
echo ""

for version in "${VERSIONS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Testing Python $version"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Install Python version if not available
    if ! uv python list | grep -q "$version"; then
        echo "Installing Python $version..."
        uv python install "$version"
    fi

    # Create and activate virtual environment for this version
    venv_dir="venvs/.venv$version"
    echo "Creating virtual environment in $venv_dir..."
    uv venv --python "$version" "$venv_dir"
    source "$venv_dir/bin/activate"

    # Print the active Python version and environment path
    echo "Active Python version:"
    python --version
    echo "Active virtual environment path:"
    echo "$VIRTUAL_ENV"
    echo "Python interpreter path:"
    which python

    # Run tests with this version
    echo "Running tests..."
    uv run --active pytest test_main.py -v

    # Quick smoke test
    echo "Testing CLI..."
    uv run --active python main.py --help > /dev/null

    echo "✅ Python $version passed!"
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 All versions passed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
