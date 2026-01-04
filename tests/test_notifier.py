"""Tests for the desktop notifier."""

from pathlib import Path
from unittest.mock import patch

from housekeeper.core.watcher import ItemType
from housekeeper.notifications.notifier import notify_new_item


@patch("housekeeper.notifications.notifier._notify_plyer")
@patch("housekeeper.notifications.notifier._notify_macos")
def test_notify_new_file(
    mock_macos: object, mock_plyer: object
) -> None:
    """Test notification for new file."""
    mock_macos.return_value = True  # type: ignore[union-attr]
    mock_plyer.return_value = True  # type: ignore[union-attr]

    path = Path("/tmp/test.txt")
    result = notify_new_item(path, ItemType.FILE)

    assert result is True


@patch("housekeeper.notifications.notifier._notify_plyer")
@patch("housekeeper.notifications.notifier._notify_macos")
def test_notify_new_directory(
    mock_macos: object, mock_plyer: object
) -> None:
    """Test notification for new directory."""
    mock_macos.return_value = True  # type: ignore[union-attr]
    mock_plyer.return_value = True  # type: ignore[union-attr]

    path = Path("/tmp/testdir")
    result = notify_new_item(path, ItemType.DIR)

    assert result is True


@patch("housekeeper.notifications.notifier._notify_plyer")
@patch("housekeeper.notifications.notifier._notify_macos")
def test_notify_returns_false_on_error(
    mock_macos: object, mock_plyer: object
) -> None:
    """Test that notify returns False when notification fails."""
    mock_macos.return_value = False  # type: ignore[union-attr]
    mock_plyer.return_value = False  # type: ignore[union-attr]

    path = Path("/tmp/test.txt")
    result = notify_new_item(path, ItemType.FILE)

    assert result is False


@patch("housekeeper.notifications.notifier._notify_plyer")
@patch("housekeeper.notifications.notifier._notify_macos")
def test_notify_calls_correct_function_based_on_platform(
    mock_macos: object, mock_plyer: object
) -> None:
    """Test that the correct notification function is called."""
    mock_macos.return_value = True  # type: ignore[union-attr]
    mock_plyer.return_value = True  # type: ignore[union-attr]

    path = Path("/tmp/test.txt")

    with patch("housekeeper.notifications.notifier.sys.platform", "darwin"):
        notify_new_item(path, ItemType.FILE)
        mock_macos.assert_called_once()  # type: ignore[union-attr]

    mock_macos.reset_mock()  # type: ignore[union-attr]
    mock_plyer.reset_mock()  # type: ignore[union-attr]

    with patch("housekeeper.notifications.notifier.sys.platform", "linux"):
        notify_new_item(path, ItemType.FILE)
        mock_plyer.assert_called_once()  # type: ignore[union-attr]