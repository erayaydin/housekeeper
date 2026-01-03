"""Tests for the desktop notifier."""

from pathlib import Path
from unittest.mock import patch

from housekeeper.core.watcher import ItemType
from housekeeper.notifications.notifier import notify_new_item


@patch("housekeeper.notifications.notifier.notification.notify")
def test_notify_new_file(mock_notify: object) -> None:
    """Test notification for new file."""
    path = Path("/tmp/test.txt")
    result = notify_new_item(path, ItemType.FILE)

    assert result is True
    mock_notify.assert_called_once()  # type: ignore[union-attr]
    call_kwargs = mock_notify.call_args.kwargs  # type: ignore[union-attr]
    assert call_kwargs["title"] == "New file detected"
    assert call_kwargs["message"] == str(path)


@patch("housekeeper.notifications.notifier.notification.notify")
def test_notify_new_directory(mock_notify: object) -> None:
    """Test notification for new directory."""
    path = Path("/tmp/testdir")
    result = notify_new_item(path, ItemType.DIR)

    assert result is True
    mock_notify.assert_called_once()  # type: ignore[union-attr]
    call_kwargs = mock_notify.call_args.kwargs  # type: ignore[union-attr]
    assert call_kwargs["title"] == "New directory detected"


@patch("housekeeper.notifications.notifier.notification.notify")
def test_notify_returns_false_on_error(mock_notify: object) -> None:
    """Test that notify returns False when notification fails."""
    mock_notify.side_effect = Exception("Notification failed")  # type: ignore[union-attr]
    path = Path("/tmp/test.txt")
    result = notify_new_item(path, ItemType.FILE)

    assert result is False