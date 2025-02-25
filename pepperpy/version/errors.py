"""
Version-related exceptions.
"""

from .types import Version


class VersionError(Exception):
    """Base class for version-related exceptions."""


class VersionParseError(VersionError):
    """Raised when a version string cannot be parsed."""

    def __init__(self, version_str: str, details: str | None = None):
        self.version_str = version_str
        self.details = details
        super().__init__(
            f"Failed to parse version string '{version_str}'"
            + (f": {details}" if details else "")
        )


class VersionCompatibilityError(VersionError):
    """Raised when versions are incompatible."""

    def __init__(
        self, version1: Version, version2: Version, details: str | None = None
    ):
        self.version1 = version1
        self.version2 = version2
        self.details = details
        super().__init__(
            f"Incompatible versions: {version1} and {version2}"
            + (f": {details}" if details else "")
        )


class VersionMigrationError(VersionError):
    """Raised when version migration fails."""

    def __init__(
        self,
        from_version: Version,
        to_version: Version,
        details: str | None = None,
    ):
        self.from_version = from_version
        self.to_version = to_version
        self.details = details
        super().__init__(
            f"Failed to migrate from version {from_version} to {to_version}"
            + (f": {details}" if details else "")
        )


class VersionValidationError(VersionError):
    """Raised when version validation fails."""

    def __init__(self, version: Version, details: str | None = None):
        self.version = version
        self.details = details
        super().__init__(
            f"Version validation failed for {version}"
            + (f": {details}" if details else "")
        )


class VersionDependencyError(VersionError):
    """Raised when there are dependency issues."""

    def __init__(self, component: str, version: Version, details: str | None = None):
        self.component = component
        self.version = version
        self.details = details
        super().__init__(
            f"Dependency error for {component} at version {version}"
            + (f": {details}" if details else "")
        )


class VersionTrackingError(VersionError):
    """Raised when version tracking fails."""

    def __init__(self, component: str, details: str | None = None):
        self.component = component
        self.details = details
        super().__init__(
            f"Version tracking failed for {component}"
            + (f": {details}" if details else "")
        )
