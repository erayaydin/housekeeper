"""Tests for the directory watcher."""

import tempfile
import time
from pathlib import Path

from housekeeper.core.watcher import DirectoryWatcher, ItemType


def test_item_type_enum() -> None:
    """Test ItemType enum values."""
    assert ItemType.FILE.name == "FILE"
    assert ItemType.DIR.name == "DIR"
    assert ItemType.FILE != ItemType.DIR


def test_watcher_detects_new_file() -> None:
    """Test that watcher detects new file creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir)
        events: list[tuple[Path, ItemType]] = []

        def on_created(path: Path, item_type: ItemType) -> None:
            events.append((path, item_type))

        watcher = DirectoryWatcher()
        watcher.watch(watch_dir, on_created)
        watcher.start()

        time.sleep(0.1)
        test_file = watch_dir / "test.txt"
        test_file.touch()
        time.sleep(0.2)

        watcher.stop()

        assert len(events) == 1
        assert events[0][0] == test_file
        assert events[0][1] == ItemType.FILE


def test_watcher_detects_new_directory() -> None:
    """Test that watcher detects new directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir)
        events: list[tuple[Path, ItemType]] = []

        def on_created(path: Path, item_type: ItemType) -> None:
            events.append((path, item_type))

        watcher = DirectoryWatcher()
        watcher.watch(watch_dir, on_created)
        watcher.start()

        time.sleep(0.1)
        test_dir = watch_dir / "testdir"
        test_dir.mkdir()
        time.sleep(0.2)

        watcher.stop()

        assert len(events) == 1
        assert events[0][0] == test_dir
        assert events[0][1] == ItemType.DIR


def test_watcher_ignores_nested_items() -> None:
    """Test that watcher ignores items created in subdirectories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir)
        subdir = watch_dir / "subdir"
        subdir.mkdir()

        events: list[tuple[Path, ItemType]] = []

        def on_created(path: Path, item_type: ItemType) -> None:
            events.append((path, item_type))

        watcher = DirectoryWatcher()
        watcher.watch(watch_dir, on_created)
        watcher.start()

        time.sleep(0.1)
        nested_file = subdir / "nested.txt"
        nested_file.touch()
        time.sleep(0.2)

        watcher.stop()

        assert len(events) == 0


def test_watcher_multiple_directories() -> None:
    """Test that watcher can watch multiple directories."""
    with tempfile.TemporaryDirectory() as tmpdir1:
        with tempfile.TemporaryDirectory() as tmpdir2:
            watch_dir1 = Path(tmpdir1)
            watch_dir2 = Path(tmpdir2)
            events: list[tuple[Path, ItemType]] = []

            def on_created(path: Path, item_type: ItemType) -> None:
                events.append((path, item_type))

            watcher = DirectoryWatcher()
            watcher.watch(watch_dir1, on_created)
            watcher.watch(watch_dir2, on_created)
            watcher.start()

            time.sleep(0.1)
            (watch_dir1 / "file1.txt").touch()
            (watch_dir2 / "file2.txt").touch()
            time.sleep(0.2)

            watcher.stop()

            assert len(events) == 2
            paths = {e[0].name for e in events}
            assert paths == {"file1.txt", "file2.txt"}


def test_watcher_is_running() -> None:
    """Test is_running method."""
    watcher = DirectoryWatcher()
    assert not watcher.is_running()

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher.watch(Path(tmpdir), lambda p, t: None)
        watcher.start()
        assert watcher.is_running()

        watcher.stop()
        assert not watcher.is_running()
