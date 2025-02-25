"""Data models for the compatibility system."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import re

from .exceptions import InvalidVersionError


@dataclass
class VersionInfo:
    """Version information with semantic versioning support."""

    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    _VERSION_PATTERN = re.compile(
        r"^(?P<major>0|[1-9]\d*)"
        r"\.(?P<minor>0|[1-9]\d*)"
        r"\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )

    @classmethod
    def from_string(cls, version: str) -> "VersionInfo":
        """Create a VersionInfo instance from a version string.
        
        Args:
            version: Version string in semantic versioning format
            
        Returns:
            VersionInfo instance
            
        Raises:
            InvalidVersionError: If the version string is invalid
        """
        match = cls._VERSION_PATTERN.match(version)
        if not match:
            raise InvalidVersionError(version)

        parts = match.groupdict()
        return cls(
            major=int(parts["major"]),
            minor=int(parts["minor"]),
            patch=int(parts["patch"]),
            prerelease=parts["prerelease"],
            build=parts["build"],
        )

    def __str__(self) -> str:
        """Convert to string representation.
        
        Returns:
            Version string in semantic versioning format
        """
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __lt__(self, other: "VersionInfo") -> bool:
        """Compare versions.
        
        Args:
            other: Version to compare with
            
        Returns:
            True if this version is less than other
        """
        if not isinstance(other, VersionInfo):
            return NotImplemented

        # Compare major.minor.patch
        for s, o in zip(
            [self.major, self.minor, self.patch],
            [other.major, other.minor, other.patch],
        ):
            if s != o:
                return s < o

        # If everything else is equal, compare pre-release
        if self.prerelease is None and other.prerelease is not None:
            return False
        if self.prerelease is not None and other.prerelease is None:
            return True
        if self.prerelease is not None and other.prerelease is not None:
            return self.prerelease < other.prerelease

        return False

    def __eq__(self, other: object) -> bool:
        """Check version equality.
        
        Args:
            other: Version to compare with
            
        Returns:
            True if versions are equal
        """
        if not isinstance(other, VersionInfo):
            return NotImplemented

        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
            and self.build == other.build
        ) 