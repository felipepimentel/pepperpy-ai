"""
Version tracking support.
"""

from .dependencies import DependencyTracker
from .history import VersionHistory, VersionHistoryEntry

__all__ = ["DependencyTracker", "VersionHistory", "VersionHistoryEntry"]
