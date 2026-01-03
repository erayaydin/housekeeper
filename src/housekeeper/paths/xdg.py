"""XDG and home directory resolution."""

from pathlib import Path

from platformdirs import (
    user_desktop_dir,
    user_documents_dir,
    user_downloads_dir,
    user_music_dir,
    user_pictures_dir,
    user_videos_dir,
)


def get_home_directory() -> Path:
    """Get the user's home directory.

    Returns:
        Path to home directory.
    """
    return Path.home()


def get_xdg_directories() -> list[Path]:
    """Get standard XDG user directories.

    Returns:
        List of XDG directory paths that exist.
    """
    xdg_funcs = [
        user_desktop_dir,
        user_documents_dir,
        user_downloads_dir,
        user_music_dir,
        user_pictures_dir,
        user_videos_dir,
    ]

    dirs = []
    for func in xdg_funcs:
        try:
            path = Path(func())
            if path.exists() and path.is_dir():
                dirs.append(path)
        except Exception:
            continue

    return dirs


def get_default_directories() -> list[Path]:
    """Get default directories to watch.

    Returns:
        List of default directory paths.
    """
    dirs = [get_home_directory()]
    dirs.extend(get_xdg_directories())
    return dirs
