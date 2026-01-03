"""Daemon runner module - invoked as subprocess to start daemon."""

import sys
import threading
from pathlib import Path

from housekeeper.config.loader import Config, load_config
from housekeeper.core.watcher import DirectoryWatcher, ItemType
from housekeeper.logging.logger import (
    get_default_log_directory,
    get_logger,
    setup_logging,
)
from housekeeper.notifications.notifier import notify_new_item
from housekeeper.paths.xdg import get_default_directories


def handle_created(path: Path, item_type: ItemType) -> None:
    """Handle a new file or directory creation."""
    logger = get_logger()
    type_label = "directory" if item_type == ItemType.DIR else "file"
    logger.info("New %s: %s", type_label, path)
    notify_new_item(path, item_type)


def run_watcher(stop_event: threading.Event) -> None:
    """Run the directory watcher until stop_event is set."""
    log_file = get_default_log_directory() / "housekeeper.log"
    logger = setup_logging(log_file=log_file)

    try:
        config = load_config()
    except FileNotFoundError:
        config = Config()

    directories = get_default_directories()
    directories.extend(Path(d).resolve() for d in config.directories)

    watcher = DirectoryWatcher()

    for directory in directories:
        if not directory.is_dir():
            logger.warning("Skipping non-directory: %s", directory)
            continue
        watcher.watch(directory, handle_created)
        logger.info("Watching: %s", directory)

    if not watcher._observer.emitters:
        logger.error("No directories to watch")
        return

    watcher.start()
    logger.info("Daemon started")

    stop_event.wait()

    logger.info("Daemon stopping")
    watcher.stop()


def main() -> int:
    """Entry point for daemon subprocess."""
    if sys.platform == "win32":
        print("Use Windows service instead", file=sys.stderr)
        return 1

    from housekeeper.daemon.unix import run_as_daemon

    run_as_daemon(run_watcher)
    return 0


if __name__ == "__main__":
    sys.exit(main())
