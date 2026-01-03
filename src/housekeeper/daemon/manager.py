"""Daemon process management."""

import os
import signal
import time
from pathlib import Path

from platformdirs import user_state_dir

from housekeeper import APP_NAME

STOP_TIMEOUT = 10


def get_pid_file_path() -> Path:
    """Get the path to the daemon PID file.

    Returns:
        Path to PID file.
    """
    return Path(user_state_dir(APP_NAME.lower())) / "daemon.pid"


def read_pid() -> int | None:
    """Read the daemon PID from file.

    Returns:
        The PID if file exists and is valid, None otherwise.
    """
    pid_file = get_pid_file_path()
    if not pid_file.exists():
        return None

    try:
        pid = int(pid_file.read_text().strip())
        return pid
    except (ValueError, OSError):
        return None


def write_pid(pid: int) -> None:
    """Write the daemon PID to file.

    Args:
        pid: Process ID to write.
    """
    pid_file = get_pid_file_path()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(pid))


def remove_pid_file() -> None:
    """Remove the PID file if it exists."""
    pid_file = get_pid_file_path()
    if pid_file.exists():
        pid_file.unlink()


def is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is running.

    Args:
        pid: Process ID to check.

    Returns:
        True if process is running, False otherwise.
    """
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop_daemon(timeout: float = STOP_TIMEOUT) -> bool:
    """Stop the running daemon.

    Args:
        timeout: Maximum time to wait for daemon to stop.

    Returns:
        True if daemon was stopped, False if not running.

    Raises:
        TimeoutError: If daemon did not stop within timeout.
    """
    pid = read_pid()
    if pid is None:
        return False

    if not is_process_running(pid):
        remove_pid_file()
        return False

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        remove_pid_file()
        return False

    start_time = time.monotonic()
    while is_process_running(pid):
        if time.monotonic() - start_time > timeout:
            raise TimeoutError(
                f"Daemon (PID {pid}) did not stop within {timeout} seconds"
            )
        time.sleep(0.1)

    remove_pid_file()
    return True


def get_daemon_status() -> tuple[bool, int | None]:
    """Get the daemon status.

    Returns:
        Tuple of (is_running, pid).
    """
    pid = read_pid()
    if pid is None:
        return False, None

    if is_process_running(pid):
        return True, pid

    remove_pid_file()
    return False, None
