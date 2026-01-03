"""Main entry point for the application."""

import argparse
import sys
import threading
from pathlib import Path

from housekeeper.core.watcher import DirectoryWatcher, ItemType

__version__ = "0.1.0"


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
        "directories",
        nargs="+",
        type=Path,
        help="directories to watch",
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


def main() -> int:
    """Run the housekeeper CLI.

    Returns:
        Exit code.
    """
    parser = create_parser()
    args = parser.parse_args()

    watcher = DirectoryWatcher()

    for directory in args.directories:
        if not directory.is_dir():
            print(f"Error: {directory} is not a directory", file=sys.stderr)
            return 1
        watcher.watch(directory.resolve(), handle_created)
        print(f"Watching: {directory.resolve()}")

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
