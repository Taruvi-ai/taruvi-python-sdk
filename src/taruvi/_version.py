"""Installed version of the taruvi package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("taruvi")
except PackageNotFoundError:  # Running from a source tree without installed metadata
    __version__ = "0.0.0"
