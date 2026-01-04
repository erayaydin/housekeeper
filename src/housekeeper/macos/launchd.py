"""macOS LaunchAgent management for auto-start functionality."""

import plistlib
import subprocess
import sys
from pathlib import Path

LAUNCH_AGENT_LABEL = "com.housekeeper.agent"


def get_launch_agent_path() -> Path:
    """Get path to the LaunchAgent plist file.

    Returns:
        Path to ~/Library/LaunchAgents/com.housekeeper.agent.plist
    """
    plist_name = f"{LAUNCH_AGENT_LABEL}.plist"
    return Path.home() / "Library" / "LaunchAgents" / plist_name


def is_frozen() -> bool:
    """Check if running as a frozen (PyInstaller) executable.

    Returns:
        True if running as frozen executable.
    """
    return getattr(sys, "frozen", False)


def is_app_bundle() -> bool:
    """Check if running inside a macOS .app bundle.

    Returns:
        True if running inside a .app bundle.
    """
    if not is_frozen():
        return False
    return ".app/Contents/MacOS" in sys.executable


def get_executable_path() -> Path:
    """Get path to the current executable.

    Works for both .app bundle and standalone CLI executable.

    Returns:
        Path to the executable.
    """
    return Path(sys.executable)


def get_program_arguments() -> list[str]:
    """Get the program arguments for the LaunchAgent.

    Returns:
        List of arguments to run the app in GUI mode.
    """
    return [str(get_executable_path()), "--gui"]


def get_log_directory() -> Path:
    """Get path to the log directory for LaunchAgent output.

    Returns:
        Path to ~/Library/Logs/Housekeeper/
    """
    log_dir = Path.home() / "Library" / "Logs" / "Housekeeper"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def create_launch_agent_plist() -> dict[str, object]:
    """Create the LaunchAgent plist dictionary.

    Returns:
        Dictionary representing the plist structure.
    """
    log_dir = get_log_directory()

    return {
        "Label": LAUNCH_AGENT_LABEL,
        "ProgramArguments": get_program_arguments(),
        "RunAtLoad": True,
        "KeepAlive": False,
        "StandardOutPath": str(log_dir / "stdout.log"),
        "StandardErrorPath": str(log_dir / "stderr.log"),
        "ProcessType": "Interactive",
    }


def install_launch_agent() -> bool:
    """Install the LaunchAgent for auto-start at login.

    Creates the plist file and loads it with launchctl.

    Returns:
        True if installation was successful.
    """
    plist_path = get_launch_agent_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)

    if is_launch_agent_loaded():
        unload_launch_agent()

    plist_data = create_launch_agent_plist()

    with plist_path.open("wb") as f:
        plistlib.dump(plist_data, f)

    return load_launch_agent()


def uninstall_launch_agent() -> bool:
    """Uninstall the LaunchAgent.

    Unloads the agent and removes the plist file.

    Returns:
        True if uninstallation was successful.
    """
    plist_path = get_launch_agent_path()

    if is_launch_agent_loaded():
        unload_launch_agent()

    if plist_path.exists():
        plist_path.unlink()
        return True

    return False


def load_launch_agent() -> bool:
    """Load the LaunchAgent using launchctl.

    Returns:
        True if loading was successful.
    """
    plist_path = get_launch_agent_path()

    if not plist_path.exists():
        return False

    try:
        subprocess.run(
            ["launchctl", "load", str(plist_path)],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def unload_launch_agent() -> bool:
    """Unload the LaunchAgent using launchctl.

    Returns:
        True if unloading was successful.
    """
    plist_path = get_launch_agent_path()

    if not plist_path.exists():
        return False

    try:
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            check=False,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def is_launch_agent_installed() -> bool:
    """Check if the LaunchAgent plist file exists.

    Returns:
        True if the plist file exists.
    """
    return get_launch_agent_path().exists()


def is_launch_agent_loaded() -> bool:
    """Check if the LaunchAgent is currently loaded.

    Returns:
        True if the agent is loaded in launchctl.
    """
    try:
        result = subprocess.run(
            ["launchctl", "list", LAUNCH_AGENT_LABEL],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


# CLI installation functions

CLI_SYMLINK_PATH = Path("/usr/local/bin/housekeeper")


def get_cli_source_path() -> Path | None:
    """Get the path to the CLI executable inside the app bundle.

    Returns:
        Path to the executable, or None if not in an app bundle.
    """
    if not is_app_bundle():
        return None
    return Path(sys.executable)


def is_cli_installed() -> bool:
    """Check if CLI symlink is installed.

    Returns:
        True if the symlink exists and points to our executable.
    """
    if not CLI_SYMLINK_PATH.exists():
        return False

    if not CLI_SYMLINK_PATH.is_symlink():
        return False

    source = get_cli_source_path()
    if source is None:
        return False

    try:
        target = CLI_SYMLINK_PATH.resolve()
        return target == source
    except OSError:
        return False


def install_cli() -> bool:
    """Install CLI symlink to /usr/local/bin.

    Requires admin privileges (will prompt for password).

    Returns:
        True if installation was successful.
    """
    source = get_cli_source_path()
    if source is None:
        return False

    CLI_SYMLINK_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        if CLI_SYMLINK_PATH.exists() or CLI_SYMLINK_PATH.is_symlink():
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'do shell script "rm -f {CLI_SYMLINK_PATH} && '
                    f'ln -s {source} {CLI_SYMLINK_PATH}" '
                    f"with administrator privileges",
                ],
                capture_output=True,
            )
        else:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'do shell script "ln -s {source} {CLI_SYMLINK_PATH}" '
                    f"with administrator privileges",
                ],
                capture_output=True,
            )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


def uninstall_cli() -> bool:
    """Remove CLI symlink.

    Requires admin privileges (will prompt for password).

    Returns:
        True if uninstallation was successful.
    """
    if not CLI_SYMLINK_PATH.exists() and not CLI_SYMLINK_PATH.is_symlink():
        return True

    try:
        result = subprocess.run(
            [
                "osascript",
                "-e",
                f'do shell script "rm -f {CLI_SYMLINK_PATH}" '
                f"with administrator privileges",
            ],
            capture_output=True,
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False
