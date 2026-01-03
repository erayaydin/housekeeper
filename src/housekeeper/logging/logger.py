"""Logging configuration for Housekeeper."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from platformdirs import user_state_dir

from housekeeper import APP_NAME

LOG_FORMAT = "[%(asctime)s] [%(process)d] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 3


def get_default_log_directory() -> Path:
    """Get the default log directory path.

    Returns:
        Path to log directory.
    """
    return Path(user_state_dir(APP_NAME.lower())) / "logs"


def setup_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
) -> logging.Logger:
    """Set up application logging.

    Args:
        level: Logging level.
        log_file: Path to log file. If None, only console logging is enabled.

    Returns:
        Configured logger.
    """
    logger = logging.getLogger(APP_NAME.lower())
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the application logger.

    Returns:
        The application logger.
    """
    return logging.getLogger(APP_NAME.lower())
