"""Unix daemon implementation using python-daemon."""

import signal
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

import daemon
from daemon import pidfile

from housekeeper.daemon.manager import get_pid_file_path, is_process_running


def run_as_daemon(
    run_func: Callable[[threading.Event], None],
    pid_path: Path | None = None,
) -> None:
    """Run a function as a daemon process.

    This function does not return in the parent - it daemonizes
    and runs the provided function.

    Args:
        run_func: Function to run. Receives a stop_event to monitor.
        pid_path: Path to PID file. If None, uses default.
    """
    if pid_path is None:
        pid_path = get_pid_file_path()

    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_lock = pidfile.PIDLockFile(str(pid_path))

    stop_event = threading.Event()

    def handle_sigterm(_signum: int, _frame: object) -> None:
        stop_event.set()

    context = daemon.DaemonContext(
        pidfile=pid_lock,
        signal_map={
            signal.SIGTERM: handle_sigterm,
        },
    )

    with context:
        run_func(stop_event)


def start_daemon_subprocess(pid_path: Path | None = None) -> int | None:
    """Start the daemon as a subprocess and return its PID.

    Args:
        pid_path: Path to PID file. If None, uses default.

    Returns:
        The daemon PID if started successfully, None otherwise.
    """
    import subprocess

    if pid_path is None:
        pid_path = get_pid_file_path()

    # Start daemon subprocess
    subprocess.Popen(
        [sys.executable, "-m", "housekeeper.daemon.runner"],
        start_new_session=True,
    )

    # Wait for PID file to be created
    for _ in range(50):  # 5 seconds max
        time.sleep(0.1)
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text().strip())
                if is_process_running(pid):
                    return pid
            except (ValueError, OSError):
                continue

    return None
