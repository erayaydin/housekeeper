"""Main entry point for the application."""

import argparse
import sys
import threading
from pathlib import Path

from housekeeper import __version__
from housekeeper.config.loader import (
    Config,
    load_config,
    save_config,
)
from housekeeper.core.watcher import DirectoryWatcher, ItemType
from housekeeper.logging.logger import (
    get_default_log_directory,
    get_logger,
    setup_logging,
)
from housekeeper.notifications.notifier import notify_new_item
from housekeeper.paths.xdg import get_default_directories

IS_WINDOWS = sys.platform == "win32"


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
        "--config",
        type=Path,
        metavar="FILE",
        help="path to config file",
    )

    subparsers = parser.add_subparsers(dest="command")

    # dirs command
    dirs_parser = subparsers.add_parser("dirs", help="manage directories")
    dirs_subparsers = dirs_parser.add_subparsers(dest="dirs_command")

    # dirs list
    dirs_subparsers.add_parser("list", help="list directories")

    # dirs add
    dirs_add_parser = dirs_subparsers.add_parser(
        "add", help="add directory to config"
    )
    dirs_add_parser.add_argument(
        "path",
        type=Path,
        help="directory path to add",
    )

    # dirs remove
    dirs_remove_parser = dirs_subparsers.add_parser(
        "remove", help="remove directory from config"
    )
    dirs_remove_parser.add_argument(
        "path",
        type=Path,
        help="directory path to remove",
    )

    # daemon command
    daemon_parser = subparsers.add_parser("daemon", help="manage daemon")
    daemon_subparsers = daemon_parser.add_subparsers(dest="daemon_command")
    daemon_subparsers.add_parser("start", help="start daemon")
    daemon_subparsers.add_parser("stop", help="stop daemon")
    daemon_subparsers.add_parser("status", help="show daemon status")
    if IS_WINDOWS:
        daemon_subparsers.add_parser("install", help="install service")
        daemon_subparsers.add_parser("uninstall", help="uninstall service")

    # Default watch arguments (when no subcommand)
    parser.add_argument(
        "--only",
        action="store_true",
        help="watch only specified directories, ignore defaults and config",
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
    logger = get_logger()
    type_label = "directory" if item_type == ItemType.DIR else "file"
    logger.info("New %s: %s", type_label, path)
    notify_new_item(path, item_type)


def cmd_dirs_list(config: Config) -> int:
    """List directories from config."""
    if not config.directories:
        print("No directories in config.")
        return 0

    for directory in config.directories:
        print(directory)
    return 0


def cmd_dirs_add(config: Config, config_path: Path | None, path: Path) -> int:
    """Add a directory to config."""
    resolved = str(path.resolve())

    if resolved in config.directories:
        print(f"Already in config: {resolved}")
        return 1

    config.directories.append(resolved)
    save_config(config, config_path)
    print(f"Added: {resolved}")
    return 0


def cmd_dirs_remove(
    config: Config, config_path: Path | None, path: Path
) -> int:
    """Remove a directory from config."""
    resolved = str(path.resolve())

    if resolved not in config.directories:
        print(f"Not in config: {resolved}")
        return 1

    config.directories.remove(resolved)
    save_config(config, config_path)
    print(f"Removed: {resolved}")
    return 0


def cmd_watch(args: argparse.Namespace, config: Config) -> int:
    """Run the watch command."""
    logger = get_logger()
    arg_dirs = args.directories or []

    if args.only:
        if arg_dirs:
            directories = [d.resolve() for d in arg_dirs]
        else:
            directories = [Path.cwd()]
    else:
        directories = get_default_directories()
        directories.extend(Path(d).resolve() for d in config.directories)
        directories.extend(d.resolve() for d in arg_dirs)

    watcher = DirectoryWatcher()

    for directory in directories:
        if not directory.is_dir():
            logger.error("Not a directory: %s", directory)
            return 1
        watcher.watch(directory, handle_created)
        logger.info("Watching: %s", directory)

    print("Press Ctrl+C to stop...")
    watcher.start()

    stop_event = threading.Event()
    try:
        stop_event.wait()
    except KeyboardInterrupt:
        print()

    print("Stopping...")
    watcher.stop()
    return 0


def cmd_daemon_start() -> int:
    """Start the daemon."""
    if IS_WINDOWS:
        from housekeeper.daemon.windows import (
            get_service_status,
            start_service,
        )

        running, _ = get_service_status()
        if running:
            print("Service already running")
            return 1

        try:
            start_service()
            print("Service started")
            return 0
        except Exception as e:
            print(f"Failed to start service: {e}", file=sys.stderr)
            return 1
    else:
        from housekeeper.daemon.manager import get_daemon_status
        from housekeeper.daemon.unix import start_daemon_subprocess

        running, pid = get_daemon_status()
        if running:
            print(f"Daemon already running (PID {pid})")
            return 1

        daemon_pid = start_daemon_subprocess()
        if daemon_pid:
            print(f"Daemon started (PID {daemon_pid})")
            return 0
        else:
            print("Failed to start daemon", file=sys.stderr)
            return 1


def cmd_daemon_stop() -> int:
    """Stop the daemon."""
    if IS_WINDOWS:
        from housekeeper.daemon.windows import get_service_status, stop_service

        running, _ = get_service_status()
        if not running:
            print("Service not running")
            return 1

        try:
            stop_service()
            print("Service stopped")
            return 0
        except Exception as e:
            print(f"Failed to stop service: {e}", file=sys.stderr)
            return 1
    else:
        from housekeeper.daemon.manager import stop_daemon

        try:
            stopped = stop_daemon()
        except TimeoutError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        if stopped:
            print("Daemon stopped")
            return 0
        else:
            print("Daemon not running")
            return 1


def cmd_daemon_status() -> int:
    """Show daemon status."""
    if IS_WINDOWS:
        from housekeeper.daemon.windows import get_service_status

        running, _ = get_service_status()
        if running:
            print("Service running")
            return 0
        else:
            print("Service not running")
            return 1
    else:
        from housekeeper.daemon.manager import get_daemon_status

        running, pid = get_daemon_status()
        if running:
            print(f"Daemon running (PID {pid})")
            return 0
        else:
            print("Daemon not running")
            return 1


def cmd_daemon_install() -> int:
    """Install Windows service."""
    if not IS_WINDOWS:
        print("Install command is only available on Windows", file=sys.stderr)
        return 1

    from housekeeper.daemon.windows import install_service

    try:
        install_service()
        print("Service installed")
        return 0
    except Exception as e:
        print(f"Failed to install service: {e}", file=sys.stderr)
        return 1


def cmd_daemon_uninstall() -> int:
    """Uninstall Windows service."""
    if not IS_WINDOWS:
        print("Uninstall is only available on Windows", file=sys.stderr)
        return 1

    from housekeeper.daemon.windows import uninstall_service

    try:
        uninstall_service()
        print("Service uninstalled")
        return 0
    except Exception as e:
        print(f"Failed to uninstall service: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Run the housekeeper CLI.

    Returns:
        Exit code.
    """
    parser = create_parser()
    args = parser.parse_args()

    log_file = get_default_log_directory() / "housekeeper.log"
    setup_logging(log_file=log_file)

    if args.command == "dirs":
        try:
            config = load_config(args.config)
        except FileNotFoundError as e:
            if args.config is not None:
                print(f"Config not found: {e}", file=sys.stderr)
                return 1
            config = Config()

        if args.dirs_command == "list":
            return cmd_dirs_list(config)
        elif args.dirs_command == "add":
            return cmd_dirs_add(config, args.config, args.path)
        elif args.dirs_command == "remove":
            return cmd_dirs_remove(config, args.config, args.path)
        else:
            parser.parse_args(["dirs", "--help"])
            return 1

    if args.command == "daemon":
        if args.daemon_command == "start":
            return cmd_daemon_start()
        elif args.daemon_command == "stop":
            return cmd_daemon_stop()
        elif args.daemon_command == "status":
            return cmd_daemon_status()
        elif args.daemon_command == "install":
            return cmd_daemon_install()
        elif args.daemon_command == "uninstall":
            return cmd_daemon_uninstall()
        else:
            parser.parse_args(["daemon", "--help"])
            return 1

    logger = get_logger()
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 1

    return cmd_watch(args, config)


if __name__ == "__main__":
    sys.exit(main())
