"""
Core types for the version management system.
"""

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar


class VersionType(Enum):
    """Type of versioning scheme being used."""

    SEMANTIC = auto()
    CALENDAR = auto()
    CUSTOM = auto()


class VersionComponent(Enum):
    """Components of a version number."""

    MAJOR = auto()
    MINOR = auto()
    PATCH = auto()
    PRE_RELEASE = auto()
    BUILD = auto()


class VersionChangeType(Enum):
    """Types of version changes."""

    MAJOR = auto()  # Breaking changes
    MINOR = auto()  # New features, backwards compatible
    PATCH = auto()  # Bug fixes, backwards compatible
    PRE_RELEASE = auto()  # Pre-release changes
    BUILD = auto()  # Build metadata changes


@dataclass(frozen=True)
class Version:
    """Immutable version object following semantic versioning."""

    major: int
    minor: int
    patch: int
    pre_release: str | None = None
    build: str | None = None

    # Regex pattern for semantic versioning
    SEMVER_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<pre>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
        r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
    )

    def __post_init__(self):
        """Validate version components after initialization."""
        if not isinstance(self.major, int) or self.major < 0:
            raise ValueError("Major version must be a non-negative integer")
        if not isinstance(self.minor, int) or self.minor < 0:
            raise ValueError("Minor version must be a non-negative integer")
        if not isinstance(self.patch, int) or self.patch < 0:
            raise ValueError("Patch version must be a non-negative integer")

        if self.pre_release is not None:
            if not isinstance(self.pre_release, str):
                raise ValueError("Pre-release identifier must be a string")
            if not re.match(r"^[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*$", self.pre_release):
                raise ValueError("Invalid pre-release identifier format")

        if self.build is not None:
            if not isinstance(self.build, str):
                raise ValueError("Build metadata must be a string")
            if not re.match(r"^[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*$", self.build):
                raise ValueError("Invalid build metadata format")

    def __str__(self) -> str:
        """Convert version to string representation."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            version += f"-{self.pre_release}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __lt__(self, other: "Version") -> bool:
        """Compare versions for sorting."""
        if not isinstance(other, Version):
            return NotImplemented

        # Compare major.minor.patch
        for s, o in zip(
            [self.major, self.minor, self.patch],
            [other.major, other.minor, other.patch],
            strict=False,
        ):
            if s != o:
                return s < o

        # Handle pre-release versions
        if self.pre_release is None and other.pre_release is not None:
            return False
        if self.pre_release is not None and other.pre_release is None:
            return True
        if self.pre_release != other.pre_release:
            return (self.pre_release or "") < (other.pre_release or "")

        return False

    def __le__(self, other: "Version") -> bool:
        """Less than or equal comparison."""
        return self < other or self == other

    def __gt__(self, other: "Version") -> bool:
        """Greater than comparison."""
        return not (self <= other)

    def __ge__(self, other: "Version") -> bool:
        """Greater than or equal comparison."""
        return not (self < other)

    def __eq__(self, other: object) -> bool:
        """Check version equality."""
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.pre_release == other.pre_release
            and self.build == other.build
        )

    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """Parse a version string into a Version object.

        Args:
            version_str (str): The version string to parse.
                Must follow semantic versioning format (e.g. "1.2.3-beta+build.123").

        Returns:
            Version: A new Version instance.

        Raises:
            ValueError: If the version string is invalid.

        Example:
            >>> Version.parse("1.2.3-beta+build.123")
            Version(major=1, minor=2, patch=3, pre_release='beta', build='build.123')
        """
        match = cls.SEMVER_PATTERN.match(version_str)
        if not match:
            raise ValueError(
                f"Version string '{version_str}' does not match semantic versioning format"
            )

        return cls(
            major=int(match.group("major")),
            minor=int(match.group("minor")),
            patch=int(match.group("patch")),
            pre_release=match.group("pre"),
            build=match.group("build"),
        )

    def increment(
        self, component: VersionComponent, pre_release: str | None = None
    ) -> "Version":
        """Create a new version by incrementing a component.

        Args:
            component (VersionComponent): The component to increment.
            pre_release (str | None): Optional pre-release identifier for the new version.

        Returns:
            Version: A new Version instance with the incremented component.

        Example:
            >>> v = Version(1, 2, 3)
            >>> v.increment(VersionComponent.MINOR)
            Version(major=1, minor=3, patch=0)
        """
        if component == VersionComponent.MAJOR:
            return Version(
                major=self.major + 1,
                minor=0,
                patch=0,
                pre_release=pre_release,
            )
        elif component == VersionComponent.MINOR:
            return Version(
                major=self.major,
                minor=self.minor + 1,
                patch=0,
                pre_release=pre_release,
            )
        elif component == VersionComponent.PATCH:
            return Version(
                major=self.major,
                minor=self.minor,
                patch=self.patch + 1,
                pre_release=pre_release,
            )
        elif component == VersionComponent.PRE_RELEASE:
            if not pre_release:
                raise ValueError("Pre-release identifier is required")
            return Version(
                major=self.major,
                minor=self.minor,
                patch=self.patch,
                pre_release=pre_release,
            )
        else:
            raise ValueError(f"Cannot increment {component.name}")


@dataclass
class VersionChange:
    """Represents a change between versions."""

    type: VersionChangeType
    description: str
    breaking: bool = False
    affected_components: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default values."""
        if self.type == VersionChangeType.MAJOR:
            self.breaking = True


@dataclass
class VersionDependency:
    """Represents a dependency between components."""

    component: str
    version: Version
    required: bool = True
    compatibility_range: tuple[Version, Version] | None = None
