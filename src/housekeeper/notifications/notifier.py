"""Desktop notification handling."""

from pathlib import Path

from plyer import notification

from housekeeper import APP_NAME
from housekeeper.core.watcher import ItemType


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
