"""Tests for path utilities."""

from pathlib import Path

from housekeeper.paths.xdg import (
    get_default_directories,
    get_home_directory,
    get_xdg_directories,
)


def test_get_home_directory() -> None:
    """Test that get_home_directory returns a valid path."""
    home = get_home_directory()
    assert isinstance(home, Path)
    assert home.exists()
    assert home.is_dir()
    assert home == Path.home()


def test_get_xdg_directories() -> None:
    """Test that get_xdg_directories returns existing directories."""
    dirs = get_xdg_directories()
    assert isinstance(dirs, list)
    for d in dirs:
        assert isinstance(d, Path)
        assert d.exists()
        assert d.is_dir()


def test_get_default_directories() -> None:
    """Test that get_default_directories includes home."""
    dirs = get_default_directories()
    assert isinstance(dirs, list)
    assert len(dirs) >= 1
    assert dirs[0] == Path.home()


def test_get_default_directories_no_duplicates() -> None:
    """Test that default directories has no duplicates."""
    dirs = get_default_directories()
    assert len(dirs) == len(set(dirs))