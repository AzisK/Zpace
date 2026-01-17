import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

from zpace.core import (
    calculate_dir_size,
    categorize_extension,
    identify_special_dir_name,
    push_top_n,
    scan_files_and_dirs,
    is_skip_path,
)
from zpace.utils import format_size
from zpace.main import print_results, main
from zpace.config import MIN_FILE_SIZE, SKIP_DIRS
from io import StringIO
import os


class TestCategorizeExtension:
    """Test file categorization."""

    def test_picture_extensions(self):
        assert categorize_extension(".jpg") == "Pictures"
        assert categorize_extension(".PNG") == "Pictures"
        assert categorize_extension(".svg") == "Pictures"
        assert categorize_extension(".heic") == "Pictures"

    def test_document_extensions(self):
        assert categorize_extension(".pdf") == "Documents"
        assert categorize_extension(".xlsx") == "Documents"
        assert categorize_extension(".txt") == "Documents"
        assert categorize_extension(".pptx") == "Documents"

    def test_code_extensions(self):
        assert categorize_extension(".py") == "Code"
        assert categorize_extension(".js") == "Code"
        assert categorize_extension(".rs") == "Code"
        assert categorize_extension(".tsx") == "Code"

    def test_video_extensions(self):
        assert categorize_extension(".mp4") == "Videos"
        assert categorize_extension(".mkv") == "Videos"
        assert categorize_extension(".webm") == "Videos"

    def test_music_extensions(self):
        assert categorize_extension(".mp3") == "Music"
        assert categorize_extension(".flac") == "Music"
        assert categorize_extension(".m4a") == "Music"

    def test_archive_extensions(self):
        assert categorize_extension(".zip") == "Archives"
        assert categorize_extension(".gz") == "Archives"
        assert categorize_extension(".7z") == "Archives"

    def test_json_yaml_extensions(self):
        assert categorize_extension(".yml") == "JSON/YAML"
        assert categorize_extension(".json") == "JSON/YAML"

    def test_unknown_extension(self):
        assert categorize_extension(".xyz") == "Others"
        assert categorize_extension("") == "Others"
        assert categorize_extension(".") == "Others"


class TestIdentifySpecialDirName:
    """Test special directory identification."""

    def test_virtual_environments(self):
        assert identify_special_dir_name(".venv") == "Virtual Environments"
        assert identify_special_dir_name("venv") == "Virtual Environments"
        assert identify_special_dir_name("env") == "Virtual Environments"

    def test_node_modules(self):
        assert identify_special_dir_name("node_modules") == "Node Modules"

    def test_git_repos(self):
        assert identify_special_dir_name(".git") == "Git Repos"

    def test_build_artifacts(self):
        assert identify_special_dir_name("target") == "Build Artifacts"
        assert identify_special_dir_name("build") == "Build Artifacts"
        assert identify_special_dir_name("dist") == "Build Artifacts"

    def test_macos_apps(self):
        assert identify_special_dir_name("Safari.app") == "macOS Apps"
        assert identify_special_dir_name("MyApp.app") == "macOS Apps"

    def test_package_caches(self):
        assert identify_special_dir_name(".npm") == "Package Caches"
        assert identify_special_dir_name(".m2") == "Package Caches"
        assert identify_special_dir_name("__pycache__") == "Package Caches"

    def test_ide_config(self):
        assert identify_special_dir_name(".idea") == "IDE Config"
        assert identify_special_dir_name(".vscode") == "IDE Config"

    def test_normal_directory(self):
        assert identify_special_dir_name("directory") is None
        assert identify_special_dir_name("documents") is None


class TestShouldSkipPath:
    """Test system directory skipping."""

    def test_linux_system_dirs(self):
        assert is_skip_path("/dev")
        assert is_skip_path("/proc")
        assert is_skip_path("/sys")

    def test_macos_system_dirs(self):
        assert is_skip_path("/System")
        assert is_skip_path("/Library")
        assert is_skip_path("/private/var")

    def test_normal_dirs(self):
        assert not is_skip_path("/home")
        assert not is_skip_path("/Users")
        assert not is_skip_path("/tmp")


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
        size = calculate_dir_size("/empty")
        assert size == 0

    def test_directory_with_files(self, fs):
        fs.create_dir("/test")
        fs.create_file("/test/file1.txt", contents="a" * 1000)
        fs.create_file("/test/file2.txt", contents="b" * 2000)

        size = calculate_dir_size("/test")
        # Should be at least the content size
        assert size >= 3000

    def test_nested_directories(self, fs):
        fs.create_dir("/test")
        fs.create_dir("/test/subdir")
        fs.create_file("/test/root.txt", contents="root" * 100)
        fs.create_file("/test/subdir/nested.txt", contents="nested" * 100)

        size = calculate_dir_size("/test")
        assert size >= 1000

    def test_nonexistent_directory(self):
        size = calculate_dir_size("/nonexistent/directory/path")
        assert size == 0

    def test_directory_with_permission_error(self, fs, monkeypatch):
        fs.create_dir("/noaccess")

        def mock_scandir(path):
            raise PermissionError("Permission denied")

        monkeypatch.setattr("os.scandir", mock_scandir)

        size = calculate_dir_size("/noaccess")
        assert size == 0


class TestPushTopN:
    """Test the min-heap top-N helper function."""

    def test_heap_not_full_adds_item(self):
        heap = []
        push_top_n(heap, (100, "/a.txt"), 3)
        push_top_n(heap, (200, "/b.txt"), 3)
        assert len(heap) == 2
        assert (100, "/a.txt") in heap
        assert (200, "/b.txt") in heap

    def test_heap_full_rejects_smaller(self):
        heap = [(100, "/a.txt"), (200, "/b.txt"), (300, "/c.txt")]
        push_top_n(heap, (50, "/small.txt"), 3)
        assert len(heap) == 3
        assert (50, "/small.txt") not in heap

    def test_heap_full_accepts_larger(self):
        heap = []
        push_top_n(heap, (100, "/a.txt"), 3)
        push_top_n(heap, (200, "/b.txt"), 3)
        push_top_n(heap, (300, "/c.txt"), 3)
        push_top_n(heap, (500, "/large.txt"), 3)
        assert len(heap) == 3
        assert (100, "/a.txt") not in heap
        assert (500, "/large.txt") in heap

    def test_heap_maintains_top_n_largest(self):
        heap = []
        sizes = [50, 300, 100, 500, 200, 400, 150]
        for i, size in enumerate(sizes):
            push_top_n(heap, (size, f"/{i}.txt"), 3)
        sorted_heap = sorted(heap, reverse=True)
        assert [s for s, _ in sorted_heap] == [500, 400, 300]

    def test_heap_size_one(self):
        heap = []
        push_top_n(heap, (100, "/a.txt"), 1)
        push_top_n(heap, (200, "/b.txt"), 1)
        push_top_n(heap, (50, "/c.txt"), 1)
        assert len(heap) == 1
        assert heap[0] == (200, "/b.txt")


class TestScanFilesAndDirs:
    """Test the main scanning functionality."""

    @patch("zpace.core.tqdm")
    def test_scan_empty_directory(self, mock_tqdm, fs):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_dir("/empty")
        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/empty"), used_bytes=100000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 0
        assert total_size == 0
        assert file_cats == {}
        assert dir_cats == {}

    @patch("zpace.core.tqdm")
    def test_scan_with_files_below_min_size(self, mock_tqdm, fs):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_file("/test/small.txt", contents="x" * 1024)  # 1KB
        fs.create_file("/test/tiny1.txt", contents="x")
        fs.create_file("/test/tiny2.jpg", contents="x")
        fs.create_file("/test/tiny3.py", contents="x")

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/test"), used_bytes=100000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 4  # File is counted
        assert total_size >= 1024  # But not categorized due to size
        assert "Documents" not in file_cats  # Too small to be categorized
        assert "Pictures" not in file_cats  # Too small to be categorized
        assert "Code" not in file_cats  # Too small to be categorized

    @patch("zpace.core.tqdm")
    def test_scan_with_categorized_files(self, mock_tqdm, fs):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create files with sufficient size to be categorized
        fs.create_file("/test/doc.pdf", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/test/image.jpg", contents="x" * MIN_FILE_SIZE)

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/test"), used_bytes=100000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 2
        assert "Documents" in file_cats
        assert "Pictures" in file_cats
        assert len(file_cats["Documents"]) == 1
        assert len(file_cats["Pictures"]) == 1

    @patch("zpace.core.tqdm")
    def test_scan_nonexistent_directory(self, mock_tqdm):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Should handle gracefully
        result = scan_files_and_dirs(Path("/nonexistent/path"), used_bytes=100000)
        # Returns empty results for nonexistent path
        assert result[2] == 0  # file_count
        assert result[3] == 0  # total_size

    @patch("zpace.core.tqdm")
    def test_complex_filesystem_scan(self, mock_tqdm, fs):
        """Test scanning a complex filesystem with various file types and directories."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

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
            Path("/test"), used_bytes=100000000, min_size=MIN_FILE_SIZE
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
        # Results are now strings in the second part of the tuple
        document_files = [os.path.basename(f[1]) for f in documents]
        assert "small.txt" not in document_files  # Should be filtered by size

    @pytest.mark.skipif(sys.platform == "win32", reason="Test specific to Unix-like systems")
    @patch("zpace.core.tqdm")
    @patch("zpace.core.is_skip_path")
    def test_skip_directories_respected(self, mock_is_skip, mock_tqdm, fs):
        """Test that system directories are properly skipped."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        def is_skip_side_effect(path_str):
            return path_str in SKIP_DIRS

        mock_is_skip.side_effect = is_skip_side_effect

        # Create files
        fs.create_file("/system.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/home/user.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/dev/should_be_skipped.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/proc/also_skipped.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/normal_dir/normal.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/home/user/user_doc.pdf", contents="x" * MIN_FILE_SIZE)

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/"), used_bytes=100000000, min_size=MIN_FILE_SIZE
        )

        # Files in skipped directories should not be included
        all_files = []
        for category_files in file_cats.values():
            all_files.extend([os.path.basename(f[1]) for f in category_files])

        assert "should_be_skipped.file" not in all_files
        assert "also_skipped.file" not in all_files
        # These should be found since they're not in skipped dirs
        assert (
            "normal.file" in all_files
            or "user.file" in all_files
            or "user_doc.pdf" in all_files
            or "system.file" in all_files
        )

    @patch("zpace.core.tqdm")
    def test_special_directories_not_descended(self, mock_tqdm, fs):
        """Test that special directories are treated as atomic units and not descended into."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create files
        fs.create_file("/project/README.md", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/project/src/main.py", contents="x" * MIN_FILE_SIZE)
        # These files inside special dirs should not be individually scanned
        fs.create_file("/project/node_modules/package.json", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/project/venv/python", contents="x" * MIN_FILE_SIZE)

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/project"), used_bytes=100000000, min_size=MIN_FILE_SIZE
        )

        # Verify special directories were categorized
        assert "Node Modules" in dir_cats
        assert "Virtual Environments" in dir_cats

        # Verify we have files from non-special directories
        assert "Code" in file_cats or "Documents" in file_cats

    @patch("zpace.core.tqdm")
    def test_mixed_file_types_and_sizes(self, mock_tqdm, fs):
        """Test scanning with mixed file types and sizes."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

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
            Path("/mixed"), used_bytes=100000000, min_size=MIN_FILE_SIZE
        )

        # Verify only files above minimum size are categorized
        assert "Pictures" not in file_cats  # small_image.jpg was too small
        assert "Code" not in file_cats  # tiny_script.py was too small

        # Verify files above threshold are properly categorized
        # At least some files should be categorized
        assert len(file_cats) > 0

    @patch("zpace.core.tqdm")
    def test_top_n_limits_results_per_category(self, mock_tqdm, fs):
        """Test that top_n limits results and returns largest items sorted descending."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create 5 documents with varying sizes
        fs.create_file("/test/doc1.pdf", contents="x" * (MIN_FILE_SIZE + 1000))
        fs.create_file("/test/doc2.pdf", contents="x" * (MIN_FILE_SIZE + 5000))
        fs.create_file("/test/doc3.pdf", contents="x" * (MIN_FILE_SIZE + 3000))
        fs.create_file("/test/doc4.pdf", contents="x" * (MIN_FILE_SIZE + 4000))
        fs.create_file("/test/doc5.pdf", contents="x" * (MIN_FILE_SIZE + 2000))

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/test"), used_bytes=100000000, min_size=MIN_FILE_SIZE, top_n=2
        )

        # Should only have 2 documents (top_n=2)
        assert len(file_cats["Documents"]) == 2
        # Should be sorted descending (largest first)
        sizes = [size for size, _ in file_cats["Documents"]]
        assert sizes[0] > sizes[1]
        # Should contain the two largest
        assert sizes[0] >= MIN_FILE_SIZE + 4000
        assert sizes[1] >= MIN_FILE_SIZE + 4000

    @patch("zpace.core.tqdm")
    def test_top_n_multiple_categories(self, mock_tqdm, fs):
        """Test that top_n applies independently to each category."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create files in multiple categories
        fs.create_file("/test/doc1.pdf", contents="x" * (MIN_FILE_SIZE + 1000))
        fs.create_file("/test/doc2.pdf", contents="x" * (MIN_FILE_SIZE + 2000))
        fs.create_file("/test/img1.jpg", contents="x" * (MIN_FILE_SIZE + 3000))
        fs.create_file("/test/img2.jpg", contents="x" * (MIN_FILE_SIZE + 4000))
        fs.create_file("/test/img3.jpg", contents="x" * (MIN_FILE_SIZE + 5000))

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/test"), used_bytes=100000000, min_size=MIN_FILE_SIZE, top_n=1
        )

        # Each category should have only 1 item (top_n=1)
        assert len(file_cats["Documents"]) == 1
        assert len(file_cats["Pictures"]) == 1
        # Each should be the largest in its category
        assert file_cats["Documents"][0][0] >= MIN_FILE_SIZE + 2000
        assert file_cats["Pictures"][0][0] >= MIN_FILE_SIZE + 5000

    @pytest.mark.skipif(sys.platform == "win32", reason="Test specific to Unix-like systems")
    @patch("zpace.core.tqdm")
    @patch("zpace.core.is_skip_path")
    def test_skip_directories_in_nested_paths(self, mock_is_skip, mock_tqdm, fs):
        """Test that system directories are skipped even when nested in scan path."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        def is_skip_side_effect(path_str):
            return path_str in SKIP_DIRS

        mock_is_skip.side_effect = is_skip_side_effect

        # Create files
        fs.create_file("/home/user/normal.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/dev/should/skip.file", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/usr/bin/binary", contents="x" * MIN_FILE_SIZE)

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/"), used_bytes=1000000, min_size=MIN_FILE_SIZE
        )

        # Collect all scanned files
        all_files = []
        for category_files in file_cats.values():
            all_files.extend([os.path.basename(f[1]) for f in category_files])

        # Files in /dev should not appear
        assert "skip.file" not in all_files
        # Files outside /dev should appear
        assert len(all_files) > 0  # Some files should be found

    @patch("zpace.core.tqdm")
    def test_only_small_files(self, mock_tqdm, fs):
        """Test directory with only files below minimum size."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_file("/small_files/tiny1.txt", contents="x")
        fs.create_file("/small_files/tiny2.jpg", contents="x")
        fs.create_file("/small_files/tiny3.py", contents="x")

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/small_files"), used_bytes=1000000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 3  # Files are still counted
        assert total_size > 0  # Size is still accumulated
        assert file_cats == {}  # But no files meet the minimum size for categorization

    @patch("zpace.core.tqdm")
    def test_deeply_nested_structure(self, mock_tqdm, fs):
        """Test scanning deeply nested directory structure."""
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_file("/deep/level1/file_at_level1.txt", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/deep/level1/level2/file_at_level2.txt", contents="x" * MIN_FILE_SIZE)
        fs.create_file(
            "/deep/level1/level2/level3/file_at_level3.txt", contents="x" * MIN_FILE_SIZE
        )
        fs.create_file(
            "/deep/level1/level2/level3/level4/file_at_level4.txt", contents="x" * MIN_FILE_SIZE
        )
        fs.create_file(
            "/deep/level1/level2/level3/level4/level5/file_at_level5.txt",
            contents="x" * MIN_FILE_SIZE,
        )

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/deep"), used_bytes=1000000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 5  # 5 levels
        assert "Documents" in file_cats
        assert len(file_cats["Documents"]) == 5


class TestPrintResults:
    """Test output formatting."""

    def test_print_empty_results(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            print_results({}, {}, 80)
            output = fake_out.getvalue()
            assert "LARGEST FILES BY CATEGORY" not in output
            assert "SPECIAL DIRECTORIES" not in output

    def test_print_populated_results(self):
        file_cats = {"Documents": [(1024, "/doc.pdf")]}
        dir_cats = {"Node Modules": [(2048, "/node_modules")]}

        with patch("sys.stdout", new=StringIO()) as fake_out:
            print_results(file_cats, dir_cats, 80)
            output = fake_out.getvalue()

            assert "LARGEST FILES BY CATEGORY" in output
            assert "SPECIAL DIRECTORIES" in output
            assert "Documents (1 files)" in output
            assert "Node Modules (1 directories)" in output
            assert "1.00 KB" in output
            assert "2.00 KB" in output


class TestMainArguments:
    """Test command line argument parsing."""

    @patch("zpace.main.scan_files_and_dirs")
    @patch("zpace.main.get_disk_usage")
    @patch("zpace.main.print_results")
    def test_default_arguments(self, mock_print, mock_disk, mock_scan):
        mock_disk.return_value = (100, 50, 50)
        mock_scan.return_value = ({}, {}, 0, 0)

        with patch("sys.argv", ["main.py"]):
            main()

            # Verify scan called with default path (home)
            args, _ = mock_scan.call_args
            assert args[0] == Path.home()

    @patch("zpace.main.scan_files_and_dirs")
    @patch("zpace.main.get_disk_usage")
    @patch("zpace.main.print_results")
    def test_custom_arguments(self, mock_print, mock_disk, mock_scan):
        mock_disk.return_value = (100, 50, 50)
        mock_scan.return_value = ({}, {}, 0, 0)

        # We need to mock Path.exists to return True for our test path
        # OR we can just use a path that we know won't be checked for existence
        # because we are mocking the scan function.
        # However, main() checks for existence before calling scan.

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_dir", return_value=True):
                test_path = "/Users/test/data"
                with patch("sys.argv", ["main.py", test_path, "--min-size", "500", "--top", "5"]):
                    main()

                    # Verify scan called with correct args
                    args, kwargs = mock_scan.call_args
                    # Compare resolved Path objects to handle OS-specific separators and drive letters
                    # main.py calls resolve(), so we must too
                    assert Path(args[0]) == Path(test_path).resolve()
                    # min_size is the 3rd positional argument (index 2)
                    assert args[2] == 500 * 1024  # KB to Bytes


class TestSymlinkHandling:
    """Test symlink handling to prevent infinite loops."""

    @patch("zpace.core.tqdm")
    def test_symlink_loop(self, mock_tqdm, fs):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create a directory structure
        fs.create_dir("/test/subdir")
        fs.create_file("/test/file.txt", contents="x" * MIN_FILE_SIZE)

        # Create a symlink pointing back to parent (loop)
        # Note: pyfakefs supports symlinks
        fs.create_symlink("/test/subdir/link_to_parent", "/test")

        # Scan should complete without infinite recursion
        # We set a timeout or just rely on the test finishing
        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/test"), used_bytes=100000, min_size=MIN_FILE_SIZE
        )

        # Should count the real file
        assert file_count == 1
        # Should NOT count the symlinked file (as we don't follow symlinks)

    @patch("zpace.core.tqdm")
    def test_symlink_to_file(self, mock_tqdm, fs):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        fs.create_file("/test/real_file.txt", contents="x" * MIN_FILE_SIZE)
        fs.create_symlink("/test/link_file.txt", "/test/real_file.txt")

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/test"), used_bytes=100000, min_size=MIN_FILE_SIZE
        )

        # Should only count the real file, not the symlink
        assert file_count == 1

    def test_symlink_rejection_in_main(self):
        """Test that main() rejects symlinks."""
        with (
            patch("sys.argv", ["main.py", "/tmp/link"]),
            patch("pathlib.Path.expanduser") as mock_expand,
            patch("pathlib.Path.is_symlink", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.resolve", return_value=Path("/real/path")),
            patch("pathlib.Path.exists", return_value=True),
            patch("zpace.main.get_disk_usage", return_value=(100, 50, 50)),
            patch("shutil.get_terminal_size") as mock_term,
            patch("sys.exit") as mock_exit,
            patch("builtins.print") as mock_print,
        ):
            mock_expand.return_value = Path("/tmp/link")
            mock_term.return_value.columns = 80

            import main as main_module

            try:
                main_module.main()
            except Exception:
                pass

            mock_exit.assert_not_called()
            mock_print.assert_any_call(f"Attention - you provided a symlink: {Path('/tmp/link')}")


class TestUnicodeHandling:
    """Test handling of unicode filenames."""

    @patch("zpace.core.tqdm")
    def test_unicode_filenames(self, mock_tqdm, fs):
        mock_pbar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        # Create files with unicode names
        fs.create_file("/test/café.txt", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/test/🚀.png", contents="x" * MIN_FILE_SIZE)
        fs.create_file("/test/こんにちは.doc", contents="x" * MIN_FILE_SIZE)

        file_cats, dir_cats, file_count, total_size = scan_files_and_dirs(
            Path("/test"), used_bytes=100000, min_size=MIN_FILE_SIZE
        )

        assert file_count == 3
        assert "Documents" in file_cats
        assert "Pictures" in file_cats

        # Verify names are preserved
        all_files = [os.path.basename(f[1]) for cat in file_cats.values() for f in cat]
        assert "café.txt" in all_files
        assert "🚀.png" in all_files
        assert "こんにちは.doc" in all_files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
