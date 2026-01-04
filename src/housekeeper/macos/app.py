"""macOS menu bar application using rumps."""

from pathlib import Path

import rumps

from housekeeper import APP_NAME, __version__
from housekeeper.config.loader import load_config
from housekeeper.core.watcher import DirectoryWatcher, ItemType
from housekeeper.logging.logger import (
    get_default_log_directory,
    get_logger,
    setup_logging,
)
from housekeeper.macos.launchd import (
    install_cli,
    install_launch_agent,
    is_app_bundle,
    is_cli_installed,
    is_launch_agent_installed,
    uninstall_cli,
    uninstall_launch_agent,
)
from housekeeper.macos.notifications import (
    notify,
    request_notification_permission,
    set_notification_delegate,
)
from housekeeper.paths.xdg import get_default_directories

FIRST_LAUNCH_KEY = "first_launch_completed"


class HousekeeperApp(rumps.App):  # type: ignore[misc]
    """Menu bar application for Housekeeper."""

    def __init__(self) -> None:
        """Initialize the menu bar application."""
        super().__init__(
            name=APP_NAME,
            title=None,
            icon=None,
            template=True,
            quit_button=None,
        )

        self._watcher: DirectoryWatcher | None = None
        self._is_watching = False
        self._config = load_config()

        self._setup_menu()

    def _setup_menu(self) -> None:
        """Set up the menu items."""
        self._status_item = rumps.MenuItem("Status: Stopped")
        self._status_item.set_callback(None)

        self._start_item = rumps.MenuItem(
            "Start Watching", callback=self._on_start
        )
        self._stop_item = rumps.MenuItem(
            "Stop Watching", callback=self._on_stop
        )
        self._stop_item.set_callback(None)

        self._dirs_menu = rumps.MenuItem("Directories")
        self._update_directories_menu()

        self._login_item = rumps.MenuItem(
            "Open at Login", callback=self._on_toggle_login
        )
        self._login_item.state = is_launch_agent_installed()

        self._cli_item = rumps.MenuItem(
            "Install CLI", callback=self._on_toggle_cli
        )
        if is_app_bundle():
            self._cli_item.state = is_cli_installed()
        else:
            self._cli_item.set_callback(None)
            self._cli_item.title = "CLI"

        self._about_item = rumps.MenuItem("About", callback=self._on_about)
        self._quit_item = rumps.MenuItem("Quit", callback=self._on_quit)

        self.menu = [
            self._status_item,
            None,
            self._start_item,
            self._stop_item,
            None,
            self._dirs_menu,
            self._login_item,
            self._cli_item,
            None,
            self._about_item,
            self._quit_item,
        ]

    def _update_directories_menu(self) -> None:
        """Update the directories submenu."""
        self._dirs_menu.clear()

        directories = self._get_all_directories()

        if not directories:
            no_dirs = rumps.MenuItem("No directories configured")
            no_dirs.set_callback(None)
            self._dirs_menu.add(no_dirs)
        else:
            for directory in directories:
                item = rumps.MenuItem(str(directory))
                item.set_callback(None)
                self._dirs_menu.add(item)

    def _get_all_directories(self) -> list[Path]:
        """Get all directories to watch.

        Returns:
            List of directory paths.
        """
        directories = get_default_directories()
        directories.extend(Path(d).resolve() for d in self._config.directories)
        return directories  # type: ignore[no-any-return]

    def _handle_created(self, path: Path, item_type: ItemType) -> None:
        """Handle a new file or directory creation.

        Args:
            path: Path to the created item.
            item_type: Type of the created item.
        """
        logger = get_logger()
        type_label = "directory" if item_type == ItemType.DIR else "file"
        logger.info("New %s: %s", type_label, path)

        title = f"New {type_label} detected"
        notify(title, str(path))

    def _on_start(self, _: rumps.MenuItem) -> None:
        """Start watching directories."""
        if self._is_watching:
            return

        logger = get_logger()
        self._watcher = DirectoryWatcher()

        directories = self._get_all_directories()

        for directory in directories:
            if directory.is_dir():
                self._watcher.watch(directory, self._handle_created)
                logger.info("Watching: %s", directory)

        self._watcher.start()
        self._is_watching = True

        self._status_item.title = "Status: Watching"
        self._start_item.set_callback(None)
        self._stop_item.set_callback(self._on_stop)

    def _on_stop(self, _: rumps.MenuItem) -> None:
        """Stop watching directories."""
        if not self._is_watching:
            return

        if self._watcher:
            self._watcher.stop()
            self._watcher = None

        self._is_watching = False

        self._status_item.title = "Status: Stopped"
        self._start_item.set_callback(self._on_start)
        self._stop_item.set_callback(None)

    def _on_toggle_login(self, sender: rumps.MenuItem) -> None:
        """Toggle open at login setting."""
        if sender.state:
            uninstall_launch_agent()
            sender.state = False
        else:
            install_launch_agent()
            sender.state = True

    def _on_toggle_cli(self, sender: rumps.MenuItem) -> None:
        """Toggle CLI installation."""
        if not is_app_bundle():
            return

        if sender.state:
            if uninstall_cli():
                sender.state = False
                rumps.notification(
                    title=APP_NAME,
                    subtitle="CLI Uninstalled",
                    message="The housekeeper command has been removed.",
                )
        else:
            if install_cli():
                sender.state = True
                rumps.notification(
                    title=APP_NAME,
                    subtitle="CLI Installed",
                    message="You can now use 'housekeeper' in Terminal.",
                )

    def _on_about(self, _: rumps.MenuItem) -> None:
        """Show about dialog."""
        rumps.alert(
            title=APP_NAME,
            message=f"Version {__version__}\n\n"
            "Protects your important directories by monitoring "
            "for new files and directories.",
            ok="OK",
        )

    def _on_quit(self, _: rumps.MenuItem) -> None:
        """Quit the application."""
        if self._is_watching:
            self._on_stop(self._stop_item)
        rumps.quit_application()

    def _check_first_launch(self) -> None:
        """Check if this is the first launch and show setup dialog."""
        from platformdirs import user_config_dir

        config_dir = Path(user_config_dir(APP_NAME.lower()))
        first_launch_file = config_dir / ".first_launch_done"

        if first_launch_file.exists():
            return

        config_dir.mkdir(parents=True, exist_ok=True)
        first_launch_file.touch()

        request_notification_permission()

        response = rumps.alert(
            title=f"Welcome to {APP_NAME}",
            message="Would you like to start Housekeeper automatically "
            "when you log in?",
            ok="Yes",
            cancel="No",
        )

        if response == 1:
            install_launch_agent()
            self._login_item.state = True

        if is_app_bundle() and not is_cli_installed():
            cli_response = rumps.alert(
                title="Install CLI?",
                message="Would you like to install the 'housekeeper' command "
                "for use in Terminal?\n\n"
                "This requires administrator privileges.",
                ok="Install",
                cancel="Skip",
            )

            if cli_response == 1 and install_cli():
                self._cli_item.state = True


def run_app() -> int:
    """Run the menu bar application.

    Returns:
        Exit code (always 0).
    """
    log_file = get_default_log_directory() / "housekeeper.log"
    setup_logging(log_file=log_file)

    set_notification_delegate()

    app = HousekeeperApp()
    app._check_first_launch()
    app._on_start(app._start_item)
    app.run()

    return 0
