"""Desktop notification handling."""

import subprocess
import sys
from pathlib import Path

from housekeeper import APP_NAME
from housekeeper.core.watcher import ItemType


def _notify_macos(title: str, message: str) -> bool:
    """Send notification on macOS using osascript."""
    script = f'display notification "{message}" with title "{title}"'
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _notify_plyer(title: str, message: str) -> bool:
    """Send notification using plyer (Linux/Windows)."""
    from plyer import notification

    try:
        notification.notify(
            title=title,
            message=message,
            app_name=APP_NAME,
            timeout=5,
        )
        return True
    except Exception:
        return False


def notify_new_item(path: Path, item_type: ItemType) -> bool:
    """Send a desktop notification for a new item.

    Args:
        path: Path to the created item.
        item_type: Type of the created item.

    Returns:
        True if notification was sent successfully.
    """
    type_label = "directory" if item_type == ItemType.DIR else "file"
    title = f"New {type_label} detected"
    message = str(path)

    if sys.platform == "darwin":
        return _notify_macos(title, message)
    else:
        return _notify_plyer(title, message)
