"""Main entry point for the application."""

import argparse
import sys
import threading
from pathlib import Path

from housekeeper import __version__
from housekeeper.core.watcher import DirectoryWatcher, ItemType
from housekeeper.notifications.notifier import notify_new_item
from housekeeper.paths.xdg import get_default_directories


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="housekeeper",
        description="Monitor directories for new files and directories.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--only",
        action="store_true",
        help="watch only specified directories, ignore defaults",
    )
    parser.add_argument(
        "directories",
        nargs="*",
        type=Path,
        help="additional directories to watch",
    )

    return parser


def handle_created(path: Path, item_type: ItemType) -> None:
    """Handle a new file or directory creation.

    Args:
        path: Path to the created item.
        item_type: Type of the created item.
    """
    type_label = "directory" if item_type == ItemType.DIR else "file"
    print(f"New {type_label}: {path}")
    notify_new_item(path, item_type)


def main() -> int:
    """Run the housekeeper CLI.

    Returns:
        Exit code.
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.only:
        if args.directories:
            directories = [d.resolve() for d in args.directories]
        else:
            directories = [Path.cwd()]
    else:
        directories = get_default_directories()
        directories.extend(d.resolve() for d in args.directories)

    watcher = DirectoryWatcher()

    for directory in directories:
        if not directory.is_dir():
            print(f"Error: {directory} is not a directory", file=sys.stderr)
            return 1
        watcher.watch(directory, handle_created)
        print(f"Watching: {directory}")

    print("Press Ctrl+C to stop...")
    watcher.start()

    stop_event = threading.Event()
    try:
        stop_event.wait()
    except KeyboardInterrupt:
        print("\nStopping...")

    watcher.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
