import pytest


def sync_func(x: int) -> int:
    return x + 1


async def async_func(x: int) -> int:
    return x + 1


def test_sync_func() -> None:
    assert sync_func(3) == 4
