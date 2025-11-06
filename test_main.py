import tempfile
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import Patcher
from unittest.mock import patch

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
        assert categorize_file("photo.jpg") == "Pictures"
        assert categorize_file("image.PNG") == "Pictures"
        assert categorize_file("graphic.svg") == "Pictures"

    def test_document_extensions(self):
        assert categorize_file("doc.pdf") == "Documents"
        assert categorize_file("sheet.xlsx") == "Documents"
        assert categorize_file("note.txt") == "Documents"

    def test_code_extensions(self):
        assert categorize_file("script.py") == "Code"
        assert categorize_file("app.js") == "Code"
        assert categorize_file("main.rs") == "Code"

    def test_video_extensions(self):
        assert categorize_file("movie.mp4") == "Videos"
        assert categorize_file("clip.mkv") == "Videos"

    def test_unknown_extension(self):
        assert categorize_file("file.xyz") == "Others"
        assert categorize_file("noext") == "Others"


class TestIdentifySpecialDir:
    """Test special directory identification."""

    def test_virtual_environments(self):
        assert identify_special_dir("/project/.venv") == "Virtual Environments"
        assert identify_special_dir("/app/venv") == "Virtual Environments"
        assert identify_special_dir("/code/env") == "Virtual Environments"

    def test_node_modules(self):
        assert identify_special_dir("/project/node_modules") == "Node Modules"

    def test_git_repos(self):
        assert identify_special_dir("/repo/.git") == "Git Repos"

    def test_build_artifacts(self):
        assert identify_special_dir("/rust/target") == "Build Artifacts"
        assert identify_special_dir("/java/build") == "Build Artifacts"
        assert identify_special_dir("/app/dist") == "Build Artifacts"

    def test_macos_apps(self):
        assert identify_special_dir("/Applications/Safari.app") == "macOS Apps"
        assert identify_special_dir("/Apps/MyApp.app") == "macOS Apps"

    def test_package_caches(self):
        assert identify_special_dir("/home/.npm") == "Package Caches"
        assert identify_special_dir("/user/.m2") == "Package Caches"
        assert identify_special_dir("/code/__pycache__") == "Package Caches"

    def test_ide_config(self):
        assert identify_special_dir("/project/.idea") == "IDE Config"
        assert identify_special_dir("/app/.vscode") == "IDE Config"

    def test_normal_directory(self):
        assert identify_special_dir("/regular/directory") is None
        assert identify_special_dir("/home/documents") is None


class TestShouldSkipDirectory:
    """Test system directory skipping."""

    def test_linux_system_dirs(self):
        assert should_skip_directory("/dev")
        assert should_skip_directory("/proc")
        assert should_skip_directory("/sys")

    def test_macos_system_dirs(self):
        assert should_skip_directory("/System")
        assert should_skip_directory("/Library")

    def test_normal_dirs(self):
        assert not should_skip_directory("/home")
        assert not should_skip_directory("/Users")
        assert not should_skip_directory("/var")


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
            size = calculate_dir_size(tmpdir)
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
        size = calculate_dir_size("/nonexistent/directory/path")
        assert size == 0


class TestFileSystem:
    @patch("main.tqdm")
    def test_file_system(self, mock_tqdm):
        # Make tqdm a no-op
        mock_tqdm.return_value.__enter__.return_value.update = lambda x: None

        with Patcher() as patcher:
            # Use the root path
            root_path = Path("/")

            # Create files in the root directory
            patcher.fs.create_file("/document.pdf", contents="pdf content" * 1000)
            patcher.fs.create_file("/image.jpg", contents="jpg content" * 1000)
            patcher.fs.create_file("/script.py", contents="python code" * 1000)

            # Create /dev directory and its files
            patcher.fs.create_dir("/dev")
            patcher.fs.create_file("/dev/music.mp3", contents="mp3 content" * 1000)
            patcher.fs.create_file("/dev/video.mp4", contents="mp4 content" * 1000)
            patcher.fs.create_file("/dev/archive.zip", contents="archive" * 1000)

            # Create /private/var directory and its file
            patcher.fs.create_dir("/private")
            patcher.fs.create_dir("/private/var")
            patcher.fs.create_file("/private/var/archive.zip", contents="archive" * 1000)

            # Create /node_modules directory and its file
            patcher.fs.create_dir("/node_modules")
            patcher.fs.create_file("/node_modules/package.json", contents="{}")

            # Call the function under test with the root path
            file_categories, dir_categories, scanned_files, scanned_size = scan_files_and_dirs(
                root_path, used=100000, min_size=1
            )

        assert set(file_categories.keys()) == {"Documents", "Code", "Pictures"}
        assert set(dir_categories.keys()) == {"Node Modules"}
        assert scanned_files == 3


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
