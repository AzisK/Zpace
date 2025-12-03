import sys
import os
from pathlib import Path
import pytest
from main import get_trash_path


class TestTrashIntegration:
    """Integration tests running on the actual OS without mocks."""

    def test_real_trash_path(self):
        """Verify get_trash_path returns the correct path for the current OS."""
        path = get_trash_path()

        if sys.platform == "darwin":
            assert path == Path.home() / ".Trash"
        elif sys.platform == "linux":
            assert path == Path.home() / ".local" / "share" / "Trash"
        elif sys.platform == "win32":
            # Windows path might vary depending on SystemDrive, but usually C:
            drive = os.environ.get("SystemDrive", "C:")
            assert path == Path(drive) / "$Recycle.Bin"
        else:
            # Fail the test if we are running on an OS we don't support yet
            pytest.fail(
                f"Unknown or unsupported OS: {sys.platform}. "
                "If you're seeing this on a supported platform, ensure your "
                "platform-specific trash directory is implemented in get_trash_path."
            )
