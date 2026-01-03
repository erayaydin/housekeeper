"""Tests for the logging module."""

import logging
import re
import tempfile
from pathlib import Path

import pytest

from housekeeper.logging.logger import (
    get_default_log_directory,
    get_logger,
    setup_logging,
)


@pytest.fixture(autouse=True)
def reset_logger() -> None:
    """Reset the housekeeper logger before each test."""
    logger = logging.getLogger("housekeeper")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)


def test_get_default_log_directory() -> None:
    """Test that get_default_log_directory returns a path."""
    log_dir = get_default_log_directory()
    assert isinstance(log_dir, Path)
    assert "housekeeper" in str(log_dir).lower()
    assert str(log_dir).endswith("logs")


def test_setup_logging_console_only() -> None:
    """Test setup_logging with console only (no file)."""
    logger = setup_logging(log_file=None)
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO
    # Should have only console handler when no file specified
    stream_handlers = [
        h for h in logger.handlers if isinstance(h, logging.StreamHandler)
    ]
    assert len(stream_handlers) >= 1


def test_setup_logging_with_file() -> None:
    """Test setup_logging with file handler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        logger = setup_logging(log_file=log_file)

        logger.info("Test message")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content
        assert "INFO" in content


def test_setup_logging_creates_parent_directory() -> None:
    """Test that setup_logging creates parent directory if needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "subdir" / "test.log"
        setup_logging(log_file=log_file)

        assert log_file.parent.exists()


def test_get_logger() -> None:
    """Test get_logger returns the application logger."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "housekeeper"


def test_log_format() -> None:
    """Test that log format matches expected pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        logger = setup_logging(log_file=log_file)

        logger.info("Format test")

        content = log_file.read_text()
        # Format: [YYYY-MM-DD HH:MM:SS] [PID] LEVEL: Message
        pattern = r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[\d+\] INFO: Format test$"
        assert re.search(pattern, content, re.MULTILINE)


def test_log_messages_not_duplicated() -> None:
    """Test that log messages appear only once in file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        logger = setup_logging(log_file=log_file)

        logger.info("Single message")

        content = log_file.read_text()
        occurrences = content.count("Single message")
        assert occurrences == 1