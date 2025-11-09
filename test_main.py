import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from main import (
    calculate_dir_size,
    categorize_file,
    format_size,
    get_top_n_per_category,
    identify_special_dir,
    scan_files_and_dirs,
    should_skip_directory,
    MIN_FILE_SIZE,
)


class TestCategorizeFile:
    """Test file categorization."""

    def test_picture_extensions(self):
        assert categorize_file(Path("photo.jpg")) == "Pictures"
        assert categorize_file(Path("image.PNG")) == "Pictures"
        assert categorize_file(Path("graphic.svg")) == "Pictures"
        assert categorize_file(Path("photo.heic")) == "Pictures"

    def test_document_extensions(self):
        assert categorize_file(Path("doc.pdf")) == "Documents"
        assert categorize_file(Path("sheet.xlsx")) == "Documents"
        assert categorize_file(Path("note.txt")) == "Documents"
        assert categorize_file(Path("presentation.pptx")) == "Documents"

    def test_code_extensions(self):
        assert categorize_file(Path("script.py")) == "Code"
        assert categorize_file(Path("app.js")) == "Code"
        assert categorize_file(Path("main.rs")) == "Code"
        assert categorize_file(Path("component.tsx")) == "Code"

    def test_video_extensions(self):
        assert categorize_file(Path("movie.mp4")) == "Videos"
        assert categorize_file(Path("clip.mkv")) == "Videos"
        assert categorize_file(Path("video.webm")) == "Videos"

    def test_music_extensions(self):
        assert categorize_file(Path("song.mp3")) == "Music"
        assert categorize_file(Path("track.flac")) == "Music"
        assert categorize_file(Path("audio.m4a")) == "Music"

    def test_archive_extensions(self):
        assert categorize_file(Path("archive.zip")) == "Archives"
        assert categorize_file(Path("compressed.tar.gz")) == "Archives"
        assert categorize_file(Path("data.7z")) == "Archives"

    def test_json_yaml_extensions(self):
        assert categorize_file(Path("config.yml")) == "JSON/YAML"
        assert categorize_file(Path("data.json")) == "JSON/YAML"

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
        assert should_skip_directory(Path("/dev"))
        assert should_skip_directory(Path("/proc"))
        assert should_skip_directory(Path("/sys"))

    def test_macos_system_dirs(self):
        assert should_skip_directory(Path("/System"))
        assert should_skip_directory(Path("/Library"))
        assert should_skip_directory(Path("/private/var"))

    def test_normal_dirs(self):
        assert not should_skip_directory(Path("/home"))
        assert not should_skip_directory(Path("/Users"))
        assert not should_skip_directory(Path("/tmp"))


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

    def test_empty_directory(self, fs):
        fs.create_dir("/empty")
        size = calculate_dir_size(Path("/empty"))
        assert size == 0

    def test_directory_with_files(self, fs):
        fs.create_dir("/test")
        fs.create_file("/test/file1.txt", contents="a" * 1000)
        fs.create_file("/test/file2.txt", contents="b" * 2000)

        size = calculate_dir_size(Path("/test"))
        # Should be at least the content size
        assert size >= 3000

    def test_nested_directories(self, fs):
        fs.create_dir("/test")
        fs.create_dir("/test/subdir")
        fs.create_file("/test/root.txt", contents="root" * 100)
        fs.create_file("/test/subdir/nested.txt", contents="nested" * 100)

        size = calculate_dir_size(Path("/test"))
        assert size > 1000

    def test_nonexistent_directory(self):
        size = calculate_dir_size(Path("/nonexistent/directory/path"))
        assert size == 0

    def test_directory_with_permission_error(self, fs, monkeypatch):
        fs.create_dir("/noaccess")

        def mock_scandir(path):
            raise PermissionError("Permission denied")

        monkeypatch.setattr("os.scandir", mock_scandir)

        size = calculate_dir_size(Path("/noaccess"))
        assert size == 0


class TestGetTopNPerCategory:
    """Test top N selection by category."""

    def test_empty_categories(self):
        result = get_top_n_per_category({})
        assert result == {}

    def test_single_category(self):
        test_data = {
            "Documents": [
                (1000, Path("small.doc")),
                (5000, Path("medium.doc")),
                (3000, Path("middle.doc")),
            ]
        }
        result = get_top_n_per_category(test_data, top_n=2)
        assert len(result["Documents"]) == 2
        assert result["Documents"][0][0] == 5000  # Largest first
        assert result["Documents"][1][0] == 3000

    def test_multiple_categories(self):
        test_data = {
            "Documents": [(1000, Path("doc1.pdf")), (2000, Path("doc2.pdf"))],
            "Pictures": [(3000, Path("img1.jpg")), (4000, Path("img2.jpg"))],
        }
        result = get_top_n_per_category(test_data, top_n=1)
        assert len(result["Documents"]) == 1
        assert len(result["Pictures"]) == 1
        assert result["Documents"][0][0] == 2000
        assert result["Pictures"][0][0] == 4000


class TestScanFilesAndDirs:
    """Test the main scanning functionality."""

    @patch("main.tqdm")
    def test_scan_empty_directory(self, mock_tqdm, fs):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_dir("/empty")
        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/empty"), used=100000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 0
        assert total_size == 0
        assert file_cats == {}
        assert dir_cats == {}

    @patch("main.tqdm")
    def test_scan_with_files_below_min_size(self, mock_tqdm, fs):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_dir("/test")
        fs.create_file("/test/small.txt", contents="x" * 1024)  # 1KB

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/test"), used=100000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 1  # File is counted
        assert total_size >= 1024  # But not categorized due to size
        assert "Documents" not in file_cats  # Too small to be categorized

    @patch("main.tqdm")
    def test_scan_with_categorized_files(self, mock_tqdm, fs):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_dir("/test")
        # Create files with sufficient size to be categorized
        fs.create_file("/test/doc.pdf", contents="x" * (MIN_FILE_SIZE + 1024))
        fs.create_file("/test/image.jpg", contents="x" * (MIN_FILE_SIZE + 2048))

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/test"), used=100000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 2
        assert "Documents" in file_cats
        assert "Pictures" in file_cats
        assert len(file_cats["Documents"]) == 1
        assert len(file_cats["Pictures"]) == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_categorize_file_nonexistent_extension(self):
        # Files with dots but no valid extension
        assert categorize_file(Path("file.")) == "Others"
        assert categorize_file(Path(".hiddenfile")) == "Others"

    @patch("main.tqdm")
    def test_scan_nonexistent_directory(self, mock_tqdm):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Should handle gracefully
        result = scan_files_and_dirs(Path("/nonexistent/path"), used=100000)
        # Returns empty results for nonexistent path
        assert result[2] == 0  # file_count
        assert result[3] == 0  # total_size


class TestRealisticFileSystem:
    """Test with a realistic filesystem structure containing various file types and directories."""

    @patch("main.tqdm")
    def test_complex_filesystem_scan(self, mock_tqdm, fs):
        """Test scanning a complex filesystem with various file types and directories."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create complex filesystem structure
        fs.create_dir("/test")
        fs.create_dir("/test/documents")
        fs.create_dir("/test/documents/subdocs")
        fs.create_dir("/test/code")
        fs.create_dir("/test/code/src")
        fs.create_dir("/test/node_modules")
        fs.create_dir("/test/venv")
        fs.create_dir("/test/dev")

        # Create files with appropriate sizes
        fs.create_file("/test/node_modules/node.js", contents="x" * (MIN_FILE_SIZE + 50000))

        fs.create_file("/test/venv/python.py", contents="x" * (MIN_FILE_SIZE + 50000))

        fs.create_file("/test/image.jpg", contents="x" * (MIN_FILE_SIZE + 50000))
        fs.create_file("/test/script.py", contents="x" * (MIN_FILE_SIZE + 10000))
        fs.create_file("/test/large_file.dat", contents="x" * (MIN_FILE_SIZE * 2))

        fs.create_file("/test/documents/report.pdf", contents="x" * (MIN_FILE_SIZE + 20000))
        fs.create_file("/test/documents/data.xlsx", contents="x" * (MIN_FILE_SIZE + 15000))
        fs.create_file("/test/documents/small.txt", contents="x")  # Small file

        fs.create_file("/test/documents/subdocs/notes.doc", contents="x" * (MIN_FILE_SIZE + 5000))

        fs.create_file("/test/code/main.js", contents="x" * (MIN_FILE_SIZE + 8000))
        fs.create_file("/test/code/config.yml", contents="x" * (MIN_FILE_SIZE + 3000))
        fs.create_file("/test/code/src/utils.py", contents="x" * (MIN_FILE_SIZE + 7000))

        fs.create_file("/test/dev/device.file", contents="x" * (MIN_FILE_SIZE + 10000))

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/test"), used=100000000, min_size=MIN_FILE_SIZE
        )

        # Verify file categories
        assert "Pictures" in file_cats
        assert "Documents" in file_cats
        assert "Code" in file_cats
        assert "JSON/YAML" in file_cats

        # Verify special directories were detected and categorized
        assert "Node Modules" in dir_cats
        assert "Virtual Environments" in dir_cats

        # Verify small file was filtered out
        documents = file_cats.get("Documents", [])
        document_files = [Path(f[1]).name for f in documents]
        assert "small.txt" not in document_files  # Should be filtered by size

    @patch("main.tqdm")
    def test_skip_directories_respected(self, mock_tqdm, fs):
        """Test that system directories are properly skipped."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create filesystem with system directories
        fs.create_dir("/")
        fs.create_dir("/home")
        fs.create_dir("/home/user")
        fs.create_dir("/private/var")
        fs.create_dir("/dev")
        fs.create_dir("/proc")
        fs.create_dir("/normal_dir")

        # Create files
        fs.create_file("/system.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/home/user.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/private/var/skipped.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/dev/should_be_skipped.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/proc/also_skipped.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/normal_dir/normal.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/home/user/user_doc.pdf", contents="x" * MIN_FILE_SIZE)

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/"), used=100000000, min_size=MIN_FILE_SIZE
        )

        # Files in skipped directories should not be included
        all_files = []
        for category_files in file_cats.values():
            all_files.extend([Path(f[1]).name for f in category_files])

        assert "skipped.file" not in all_files
        assert "should_be_skipped.file" not in all_files
        assert "also_skipped.file" not in all_files
        # These should be found since they're not in skipped dirs
        assert (
            "normal.file" in all_files
            or "user.file" in all_files
            or "user_doc.pdf" in all_files
            or "system.file" in all_files
        )


class TestSpecialDirectoryHandling:
    """Test special directory detection and handling."""

    @patch("main.tqdm")
    def test_special_directories_not_descended(self, mock_tqdm, fs):
        """Test that special directories are treated as atomic units and not descended into."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create project structure with special directories
        fs.create_dir("/project")
        fs.create_dir("/project/src")
        fs.create_dir("/project/node_modules")
        fs.create_dir("/project/venv")

        # Create files
        fs.create_file("/project/README.md", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/project/src/main.py", contents="x" * MIN_FILE_SIZE)
        # These files inside special dirs should not be individually scanned
        fs.create_file("/project/node_modules/package.json", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/project/venv/python", contents="x" * MIN_FILE_SIZE)

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/project"), used=100000000, min_size=MIN_FILE_SIZE
        )

        # Verify special directories were categorized
        assert "Node Modules" in dir_cats
        assert "Virtual Environments" in dir_cats

        # Verify we have files from non-special directories
        assert "Code" in file_cats or "Documents" in file_cats

    @patch("main.tqdm")
    def test_mixed_file_types_and_sizes(self, mock_tqdm, fs):
        """Test scanning with mixed file types and sizes."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_dir("/mixed")

        # Create files with different sizes
        fs.create_file("/mixed/huge_video.mp4", contents="x" * (MIN_FILE_SIZE * 10))
        fs.create_file(
            "/mixed/small_image.jpg", contents="x" * (MIN_FILE_SIZE // 2)
        )  # Below threshold
        fs.create_file("/mixed/medium_doc.pdf", contents="x" * (MIN_FILE_SIZE + 5000))
        fs.create_file("/mixed/config.json", contents="x" * (MIN_FILE_SIZE + 2000))
        fs.create_file(
            "/mixed/tiny_script.py", contents="x" * (MIN_FILE_SIZE // 3)
        )  # Below threshold
        fs.create_file("/mixed/large_archive.zip", contents="x" * (MIN_FILE_SIZE * 5))

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/mixed"), used=100000000, min_size=MIN_FILE_SIZE
        )

        # Verify only files above minimum size are categorized
        assert "Pictures" not in file_cats  # small_image.jpg was too small
        assert "Code" not in file_cats  # tiny_script.py was too small

        # Verify files above threshold are properly categorized
        # At least some files should be categorized
        assert len(file_cats) > 0


class TestSystemDirectoryBehavior:
    """Test behavior with system directories."""

    def test_skip_directory_detection(self):
        """Verify system directories are correctly identified."""
        assert should_skip_directory(Path("/dev")) is True
        assert should_skip_directory(Path("/proc")) is True
        assert should_skip_directory(Path("/System")) is True
        assert should_skip_directory(Path("/Library")) is True
        assert should_skip_directory(Path("/home/user")) is False
        assert should_skip_directory(Path("/tmp")) is False

    @patch("main.tqdm")
    def test_skip_directories_in_nested_paths(self, mock_tqdm, fs):
        """Test that system directories are skipped even when nested in scan path."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create filesystem structure
        fs.create_dir("/")
        fs.create_dir("/home")
        fs.create_dir("/home/user")
        fs.create_dir("/dev")
        fs.create_dir("/dev/notnull")
        fs.create_dir("/usr")
        fs.create_dir("/usr/bin")

        # Create files
        fs.create_file("/home/user/normal.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/dev/notnull/should_skip.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/usr/bin/binary", contents="x" * MIN_FILE_SIZE)

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/"), used=1000000, min_size=MIN_FILE_SIZE
        )

        # Collect all scanned files
        all_files = []
        for category_files in file_cats.values():
            all_files.extend([Path(f[1]).name for f in category_files])

        # Files in /dev should not appear
        assert "should_skip.file" not in all_files
        # Files outside /dev should appear
        assert len(all_files) > 0  # Some files should be found


class TestComprehensiveScenarios:
    """Comprehensive test scenarios covering various edge cases."""

    @patch("main.tqdm")
    def test_empty_directories(self, mock_tqdm, fs):
        """Test scanning empty directories."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_dir("/empty")

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/empty"), used=100000000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 0
        assert total_size == 0
        assert file_cats == {}
        assert dir_cats == {}

    @patch("main.tqdm")
    def test_only_small_files(self, mock_tqdm, fs):
        """Test directory with only files below minimum size."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_dir("/small_files")
        fs.create_file("/small_files/tiny1.txt", contents="x")
        fs.create_file("/small_files/tiny2.jpg", contents="x")
        fs.create_file("/small_files/tiny3.py", contents="x")

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/small_files"), used=1000000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 3  # Files are still counted
        assert total_size > 0  # Size is still accumulated
        assert file_cats == {}  # But no files meet the minimum size for categorization

    @patch("main.tqdm")
    def test_deeply_nested_structure(self, mock_tqdm, fs):
        """Test scanning deeply nested directory structure."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create deep nesting
        current_path = "/deep"
        fs.create_dir(current_path)
        fs.create_file(f"{current_path}/root_file.txt", contents="x" * (MIN_FILE_SIZE + 1000))

        for i in range(1, 6):  # 5 levels deep
            current_path = f"/deep/level{i}"
            fs.create_dir(current_path)
            fs.create_file(
                f"{current_path}/file_at_level{i}.txt", contents="x" * (MIN_FILE_SIZE + 1000)
            )

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/deep"), used=100000000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 6  # root + 5 levels
        assert "Documents" in file_cats
        assert len(file_cats["Documents"]) == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
