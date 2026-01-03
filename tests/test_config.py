"""Tests for the configuration module."""

import tempfile
from pathlib import Path

import pytest

from housekeeper.config.loader import (
    Config,
    get_default_config_path,
    load_config,
    save_config,
)


def test_config_defaults() -> None:
    """Test that Config has sensible defaults."""
    config = Config()
    assert config.directories == []


def test_get_default_config_path() -> None:
    """Test that get_default_config_path returns a valid path."""
    config_path = get_default_config_path()
    assert isinstance(config_path, Path)
    assert "housekeeper" in str(config_path).lower()
    assert config_path.name == "config.toml"


def test_load_config_explicit_path_missing_raises() -> None:
    """Test that loading explicit nonexistent config raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "nonexistent.toml"
        with pytest.raises(FileNotFoundError):
            load_config(config_path)


def test_load_config_empty_file() -> None:
    """Test loading config from empty TOML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        config_path.write_text("")
        config = load_config(config_path)
        assert config.directories == []


def test_load_config_with_directories() -> None:
    """Test loading config with directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        config_path.write_text('directories = ["/home/user/Downloads", "/tmp"]')
        config = load_config(config_path)
        assert config.directories == ["/home/user/Downloads", "/tmp"]


def test_save_config_creates_file() -> None:
    """Test that save_config creates the config file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        config = Config(directories=["/home/user/Test"])
        save_config(config, config_path)
        assert config_path.exists()


def test_save_config_creates_parent_directory() -> None:
    """Test that save_config creates parent directories if needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "subdir" / "config.toml"
        config = Config()
        save_config(config, config_path)
        assert config_path.parent.exists()
        assert config_path.exists()


def test_save_and_load_config_roundtrip() -> None:
    """Test that saving and loading config preserves data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        original = Config(directories=["/home/user/One", "/home/user/Two"])
        save_config(original, config_path)
        loaded = load_config(config_path)
        assert loaded.directories == original.directories


def test_load_config_ignores_unknown_keys() -> None:
    """Test that unknown keys in config are ignored."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        config_path.write_text("""
directories = ["/tmp"]
unknown_key = "value"
another_unknown = 123
""")
        config = load_config(config_path)
        assert config.directories == ["/tmp"]