"""Windows service implementation using pywin32."""

from pathlib import Path

import servicemanager
import win32event
import win32service
import win32serviceutil

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


class HousekeeperService(win32serviceutil.ServiceFramework):
    """Windows service for Housekeeper."""

    _svc_name_ = "Housekeeper"
    _svc_display_name_ = "Housekeeper Directory Monitor"
    _svc_description_ = "Monitors directories for new files and directories"

    def __init__(self, args: list[str]) -> None:
        """Initialize the service."""
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.watcher: DirectoryWatcher | None = None

    def SvcStop(self) -> None:  # noqa: N802
        """Stop the service."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.watcher:
            self.watcher.stop()

    def SvcDoRun(self) -> None:  # noqa: N802
        """Run the service."""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )

        log_file = get_default_log_directory() / "housekeeper.log"
        logger = setup_logging(log_file=log_file)

        try:
            config = load_config()
        except FileNotFoundError:
            config = Config()

        directories = get_default_directories()
        directories.extend(Path(d).resolve() for d in config.directories)

        self.watcher = DirectoryWatcher()

        for directory in directories:
            if not directory.is_dir():
                logger.warning("Skipping non-directory: %s", directory)
                continue
            self.watcher.watch(directory, handle_created)
            logger.info("Watching: %s", directory)

        if not self.watcher._observer.emitters:
            logger.error("No directories to watch")
            return

        self.watcher.start()
        logger.info("Service started")

        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

        logger.info("Service stopping")
        self.watcher.stop()


def install_service() -> None:
    """Install the Windows service."""
    win32serviceutil.InstallService(
        HousekeeperService._svc_reg_class_,  # type: ignore[attr-defined]
        HousekeeperService._svc_name_,
        HousekeeperService._svc_display_name_,
        startType=win32service.SERVICE_AUTO_START,
        description=HousekeeperService._svc_description_,
    )


def uninstall_service() -> None:
    """Uninstall the Windows service."""
    win32serviceutil.RemoveService(HousekeeperService._svc_name_)


def start_service() -> None:
    """Start the Windows service."""
    win32serviceutil.StartService(HousekeeperService._svc_name_)


def stop_service() -> None:
    """Stop the Windows service."""
    win32serviceutil.StopService(HousekeeperService._svc_name_)


def get_service_status() -> tuple[bool, int | None]:
    """Get the service status.

    Returns:
        Tuple of (is_running, status_code).
    """
    try:
        status = win32serviceutil.QueryServiceStatus(
            HousekeeperService._svc_name_
        )
        is_running = status[1] == win32service.SERVICE_RUNNING
        return is_running, status[1]
    except Exception:
        return False, None


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(HousekeeperService)
