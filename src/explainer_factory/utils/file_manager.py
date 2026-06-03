"""File and directory management utilities."""

import os
import shutil
from pathlib import Path

from explainer_factory.logging import get_logger

logger = get_logger(__name__)


def clean_directory(dir_path: Path, ignore_errors: bool = True) -> None:
    """Safely remove a directory and all its contents.

    Args:
        dir_path: Directory to remove.
        ignore_errors: Whether to ignore errors during removal.
    """
    if dir_path.exists() and dir_path.is_dir():
        try:
            shutil.rmtree(dir_path, ignore_errors=ignore_errors)
            logger.debug("utils.file_manager.cleaned_dir", dir=str(dir_path))
        except OSError as e:
            logger.error(
                "utils.file_manager.clean_error",
                dir=str(dir_path),
                error=str(e),
            )


def ensure_dir(dir_path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_project_root() -> Path:
    """Get the absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent
