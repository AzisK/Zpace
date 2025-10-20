#!/bin/bash
# Quick local test script for multiple Python versions
# For CI/CD, use GitHub Actions instead

set -e

VERSIONS=("3.9" "3.10" "3.11" "3.12" "3.13")

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

    # Run tests with this version
    echo "Running tests..."
    uv run --python "$version" pytest test_main.py -v

    # Quick smoke test
    echo "Testing CLI..."
    uv run --python "$version" python main.py --help > /dev/null

    echo "✅ Python $version passed!"
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 All versions passed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
