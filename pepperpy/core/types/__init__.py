"""Core types for the PepperPy framework"""

# Import basic types
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

# Define common type aliases
PathLike = Union[str, bytes]
JsonDict = Dict[str, Any]
JsonList = List[Any]


class VersionChangeType(Enum):
    """Types of version changes."""

    MAJOR = auto()
    MINOR = auto()
    PATCH = auto()
    PRE_RELEASE = auto()
    BUILD = auto()


class VersionComponent(Enum):
    """Components of a version."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRE_RELEASE = "pre_release"
    BUILD = "build"


@dataclass
class Version:
    """Semantic version representation."""

    major: int
    minor: int
    patch: int
    pre_release: Optional[str] = None
    build: Optional[str] = None

    def __str__(self) -> str:
        """Convert version to string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            version += f"-{self.pre_release}"
        if self.build:
            version += f"+{self.build}"
        return version

    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """Parse version string into Version object."""
        # Split version into parts
        if "+" in version_str:
            version_part, build = version_str.split("+", 1)
        else:
            version_part, build = version_str, None

        if "-" in version_part:
            version_part, pre_release = version_part.split("-", 1)
        else:
            pre_release = None

        # Parse version numbers
        parts = version_part.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")

        try:
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])
        except ValueError:
            raise ValueError(f"Invalid version format: {version_str}")

        return cls(
            major=major,
            minor=minor,
            patch=patch,
            pre_release=pre_release,
            build=build,
        )


@dataclass
class VersionChange:
    """Represents a change between versions."""

    type: VersionChangeType
    description: str
    breaking: bool = False
    affected_components: List[str] = field(default_factory=list)


@dataclass
class VersionDependency:
    """Represents a dependency on a specific version or version range."""

    component: str
    version: Version
    required: bool = True
    compatibility_range: Optional[Tuple[Version, Version]] = None
    description: Optional[str] = None


__all__ = [
    "PathLike",
    "JsonDict",
    "JsonList",
    "Version",
    "VersionChange",
    "VersionChangeType",
    "VersionComponent",
    "VersionDependency",
]
