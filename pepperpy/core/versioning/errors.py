"""Error definitions for the versioning system.

This module defines the exceptions used by the versioning components:

- VersionError: Base class for all versioning errors
- InvalidVersionError: Raised when a version string is invalid
- VersionMismatchError: Raised when versions are incompatible
- VersionConstraintError: Raised when a version constraint cannot be satisfied
- VersionResolutionError: Raised when version resolution fails
- MigrationError: Raised when migration between versions fails

These exceptions provide clear error handling and reporting for version-related
operations throughout the framework.
"""

from typing import Any, List, Optional


class VersionError(Exception):
    """Base class for all versioning errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidVersionError(VersionError):
    """Raised when a version string is invalid."""

    def __init__(self, version_str: str, reason: Optional[str] = None):
        self.version_str = version_str
        self.reason = reason
        message = f"Invalid version string: '{version_str}'"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class VersionMismatchError(VersionError):
    """Raised when versions are incompatible."""

    def __init__(self, version1: Any, version2: Any, context: Optional[str] = None):
        self.version1 = version1
        self.version2 = version2
        self.context = context
        message = f"Version mismatch: {version1} is not compatible with {version2}"
        if context:
            message += f" in context: {context}"
        super().__init__(message)


class VersionConstraintError(VersionError):
    """Raised when a version constraint cannot be satisfied."""

    def __init__(self, constraint: Any, version: Any, reason: Optional[str] = None):
        self.constraint = constraint
        self.version = version
        self.reason = reason
        message = f"Version constraint not satisfied: {constraint} not met by {version}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class VersionResolutionError(VersionError):
    """Raised when version resolution fails."""

    def __init__(self, constraints: List[Any], reason: Optional[str] = None):
        self.constraints = constraints
        self.reason = reason
        message = f"Failed to resolve version constraints: {constraints}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class MigrationError(VersionError):
    """Raised when migration between versions fails."""

    def __init__(
        self, source_version: Any, target_version: Any, reason: Optional[str] = None,
    ):
        self.source_version = source_version
        self.target_version = target_version
        self.reason = reason
        message = f"Migration failed from {source_version} to {target_version}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


# Export all exceptions
__all__ = [
    "InvalidVersionError",
    "MigrationError",
    "VersionConstraintError",
    "VersionError",
    "VersionMismatchError",
    "VersionResolutionError",
]
