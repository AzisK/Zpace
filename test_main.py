import tempfile
from pathlib import Path

import pytest

from main import (
    calculate_dir_size,
    categorize_file,
    format_size,
    identify_special_dir,
    scan_files_and_dirs,
    should_skip_directory,
)


class TestCategorizeFile:
    """Test file categorization."""

    def test_picture_extensions(self):
        assert categorize_file(Path("photo.jpg")) == "Pictures"
        assert categorize_file(Path("image.PNG")) == "Pictures"
        assert categorize_file(Path("graphic.svg")) == "Pictures"

    def test_document_extensions(self):
        assert categorize_file(Path("doc.pdf")) == "Documents"
        assert categorize_file(Path("sheet.xlsx")) == "Documents"
        assert categorize_file(Path("note.txt")) == "Documents"

    def test_code_extensions(self):
        assert categorize_file(Path("script.py")) == "Code"
        assert categorize_file(Path("app.js")) == "Code"
        assert categorize_file(Path("main.rs")) == "Code"

    def test_video_extensions(self):
        assert categorize_file(Path("movie.mp4")) == "Videos"
        assert categorize_file(Path("clip.mkv")) == "Videos"

    def test_unknown_extension(self):
        assert categorize_file(Path("file.xyz")) == "Others"
        assert categorize_file(Path("noext")) == "Others"


class TestIdentifySpecialDir:
    """Test special directory identification."""

    def test_virtual_environments(self):
        assert identify_special_dir(Path("/project/.venv")) == "Virtual Environments"
        assert identify_special_dir(Path("/app/venv")) == "Virtual Environments"
        assert identify_special_dir(Path("/code/env")) == "Virtual Environments"

    def test_node_modules(self):
        assert identify_special_dir(Path("/project/node_modules")) == "Node Modules"

    def test_git_repos(self):
        assert identify_special_dir(Path("/repo/.git")) == "Git Repos"

    def test_build_artifacts(self):
        assert identify_special_dir(Path("/rust/target")) == "Build Artifacts"
        assert identify_special_dir(Path("/java/build")) == "Build Artifacts"
        assert identify_special_dir(Path("/app/dist")) == "Build Artifacts"

    def test_macos_apps(self):
        assert identify_special_dir(Path("/Applications/Safari.app")) == "macOS Apps"
        assert identify_special_dir(Path("/Apps/MyApp.app")) == "macOS Apps"

    def test_package_caches(self):
        assert identify_special_dir(Path("/home/.npm")) == "Package Caches"
        assert identify_special_dir(Path("/user/.m2")) == "Package Caches"
        assert identify_special_dir(Path("/code/__pycache__")) == "Package Caches"

    def test_ide_config(self):
        assert identify_special_dir(Path("/project/.idea")) == "IDE Config"
        assert identify_special_dir(Path("/app/.vscode")) == "IDE Config"

    def test_normal_directory(self):
        assert identify_special_dir(Path("/regular/directory")) is None
        assert identify_special_dir(Path("/home/documents")) is None


class TestShouldSkipDirectory:
    """Test system directory skipping."""

    def test_linux_system_dirs(self):
        assert should_skip_directory(Path("/dev/sda1"))
        assert should_skip_directory(Path("/proc/cpuinfo"))
        assert should_skip_directory(Path("/sys/class"))

    def test_macos_system_dirs(self):
        assert should_skip_directory(Path("/System/Library"))
        assert should_skip_directory(Path("/Library/System"))

    def test_normal_dirs(self):
        assert not should_skip_directory(Path("/home/user"))
        assert not should_skip_directory(Path("/Users/admin"))
        assert not should_skip_directory(Path("/var/www"))


class TestFormatSize:
    """Test size formatting."""

    def test_bytes(self):
        assert format_size(0) == "0.00 B"
        assert format_size(500) == "500.00 B"
        assert format_size(1023) == "1023.00 B"

    def test_kilobytes(self):
        assert format_size(1024) == "1.00 KB"
        assert format_size(1536) == "1.50 KB"

    def test_megabytes(self):
        assert format_size(1024 * 1024) == "1.00 MB"
        assert format_size(1024 * 1024 * 5) == "5.00 MB"

    def test_gigabytes(self):
        assert format_size(1024 * 1024 * 1024) == "1.00 GB"
        assert format_size(1024 * 1024 * 1024 * 2.5) == "2.50 GB"

    def test_terabytes(self):
        assert format_size(1024 * 1024 * 1024 * 1024) == "1.00 TB"


class TestCalculateDirSize:
    """Test directory size calculation."""

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            size = calculate_dir_size(Path(tmpdir))
            assert size == 0

    def test_directory_with_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create test files
            (tmp_path / "file1.txt").write_text("a" * 1000)
            (tmp_path / "file2.txt").write_text("b" * 2000)

            size = calculate_dir_size(tmp_path)
            # Size should be at least the content size but most file systems allocate space in blocks (e.g. 4KB per block)
            # Metadata: The directory itself and file metadata (permissions, timestamps, etc.) also consume space.
            # So, the total space used will likely be 8KB or more, even though the content is only 3KB.
            assert size >= 3000

    def test_nested_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create nested structure
            subdir = tmp_path / "subdir"
            subdir.mkdir()
            (tmp_path / "root.txt").write_text("root" * 100)
            (subdir / "nested.txt").write_text("nested" * 100)

            size = calculate_dir_size(tmp_path)
            assert size > 1000

    def test_nonexistent_directory(self):
        size = calculate_dir_size(Path("/nonexistent/directory/path"))
        assert size == 0


class TestApp:
    def test_scan_small_directory(self):
        """Test scanning a small directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create test structure
            (tmp_path / "document.pdf").write_text("pdf content" * 1000)
            (tmp_path / "image.jpg").write_text("jpg content" * 1000)
            (tmp_path / "script.py").write_text("python code" * 1000)

            # Create node_modules
            node_modules = tmp_path / "node_modules"
            node_modules.mkdir()
            (node_modules / "package.json").write_text("{}")

            file_categories, dir_categories, scanned_files, scanned_size = scan_files_and_dirs(
                tmp_path, used=100000, min_size=1
            )

            # Test that we can identify the special dir
            assert list(file_categories.keys()) == ["Documents", "Code", "Pictures"]
            assert list(dir_categories.keys()) == ["Node Modules"]
            assert scanned_files == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
