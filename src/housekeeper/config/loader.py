"""Configuration file loading and saving."""

from dataclasses import dataclass, field
from pathlib import Path

import tomli_w
import tomllib
from platformdirs import user_config_dir

from housekeeper import APP_NAME


@dataclass
class Config:
    """Application configuration."""

    directories: list[str] = field(default_factory=list)


def get_default_config_path() -> Path:
    """Get the default configuration file path.

    Returns:
        Path to config file.
    """
    return Path(user_config_dir(APP_NAME.lower())) / "config.toml"


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file.

    Args:
        config_path: Path to config file. If None, uses default location.

    Returns:
        Loaded configuration.

    Raises:
        FileNotFoundError: If explicit config path doesn't exist.
    """
    if config_path is None:
        path = get_default_config_path()
        if not path.exists():
            return Config()
    else:
        path = config_path
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("rb") as f:
        data = tomllib.load(f)

    return Config(
        directories=data.get("directories", []),
    )


def save_config(config: Config, config_path: Path | None = None) -> None:
    """Save configuration to file.

    Args:
        config: Configuration to save.
        config_path: Path to config file. If None, uses default location.
    """
    if config_path is None:
        config_path = get_default_config_path()

    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "directories": config.directories,
    }

    with config_path.open("wb") as f:
        tomli_w.dump(data, f)
