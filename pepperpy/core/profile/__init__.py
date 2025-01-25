"""Profile module for managing AI profiles.

This module provides functionality for managing AI profiles,
including preferences, settings, history tracking, and persistence.
"""

from .profile import (
    ProfileError,
    Profile,
)
from .manager import (
    ManagerError,
    ProfileManager,
)

__all__ = [
    "ProfileError",
    "Profile",
    "ManagerError",
    "ProfileManager",
]
