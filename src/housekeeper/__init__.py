"""Housekeeper - Monitor directories for new files and directories."""

from importlib.metadata import metadata

_metadata = metadata("housekeeper")

__version__ = _metadata["Version"]
APP_NAME = _metadata["Name"].title()

__all__ = ["APP_NAME", "__version__"]
