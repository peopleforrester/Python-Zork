"""
KodeKloud Computer Quest

An educational text-based adventure game that teaches computer architecture concepts.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _dist_version

try:
    __version__ = _dist_version("computerquest")
except PackageNotFoundError:
    # Fallback for source checkouts where the dist metadata isn't installed.
    __version__ = "0.0.0+local"

__author__ = "Michael Forrester"
__license__ = "MIT"
