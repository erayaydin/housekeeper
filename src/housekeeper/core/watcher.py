"""Directory watcher using watchdog."""

from collections.abc import Callable
from enum import Enum, auto
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class ItemType(Enum):
    """Type of filesystem item."""

    FILE = auto()
    DIR = auto()


class CreationEventHandler(FileSystemEventHandler):
    """Handle file and directory creation events."""

    def __init__(
        self,
        watched_dir: Path,
        on_created: Callable[[Path, ItemType], None],
    ) -> None:
        """Initialize the event handler.

        Args:
            watched_dir: The directory being watched.
            on_created: Callback for creation events. Takes path and item type.
        """
        super().__init__()
        self._watched_dir = watched_dir
        self._on_created = on_created

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle creation events.

        Args:
            event: The filesystem event.
        """
        src_path = event.src_path
        if isinstance(src_path, bytes):
            src_path = src_path.decode()
        path = Path(src_path)

        if path.parent != self._watched_dir:
            return

        item_type = ItemType.DIR if event.is_directory else ItemType.FILE
        self._on_created(path, item_type)


class DirectoryWatcher:
    """Watch directories for new files and directories."""

    def __init__(self) -> None:
        """Initialize the watcher."""
        self._observer = Observer()
        self._running = False

    def watch(
        self,
        directory: Path,
        on_created: Callable[[Path, ItemType], None],
    ) -> None:
        """Add a directory to watch.

        Args:
            directory: The directory to watch.
            on_created: Callback for creation events.
        """
        handler = CreationEventHandler(directory, on_created)
        # recursive=True needed for macOS FSEvents to detect directory creation
        # parent check in handler ensures only top-level items are reported
        self._observer.schedule(handler, str(directory), recursive=True)

    def start(self) -> None:
        """Start watching."""
        self._observer.start()
        self._running = True

    def stop(self) -> None:
        """Stop watching."""
        self._observer.stop()
        self._observer.join()
        self._running = False

    def is_running(self) -> bool:
        """Check if watcher is running.

        Returns:
            True if running, False otherwise.
        """
        return self._running
