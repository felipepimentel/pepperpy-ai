"""Version compatibility checking system.

This module provides functionality for checking compatibility between different versions:

- CompatibilityChecker: Core class for checking version compatibility
- Version range specification and validation
- Breaking change detection and tracking
- Compatibility matrices for complex version relationships
- Compatibility policies for different upgrade scenarios

The compatibility system enables applications to determine if different versions
can work together, facilitating safe upgrades and component integration.
"""

from typing import Any, Optional

from ..errors import VersionCompatibilityError
from ..types import Version, VersionChange, VersionChangeType


class VersionRange:
    """Represents a range of versions."""

    def __init__(
        self,
        min_version: Optional[Version] = None,
        max_version: Optional[Version] = None,
        include_min: bool = True,
        include_max: bool = False,
    ) -> None:
        """Initialize version range.

        Args:
            min_version: Minimum version (inclusive by default)
            max_version: Maximum version (exclusive by default)
            include_min: Whether to include min_version in the range
            include_max: Whether to include max_version in the range
        """
        self.min_version = min_version
        self.max_version = max_version
        self.include_min = include_min
        self.include_max = include_max

    def contains(self, version: Version) -> bool:
        """Check if version is in range.

        Args:
            version: Version to check

        Returns:
            True if version is in range
        """
        if self.min_version:
            if version.major < self.min_version.major:
                return False
            if version.major == self.min_version.major:
                if version.minor < self.min_version.minor:
                    return False
                if version.minor == self.min_version.minor:
                    if version.patch < self.min_version.patch:
                        return False
                    if version.patch == self.min_version.patch and not self.include_min:
                        return False

        if self.max_version:
            if version.major > self.max_version.major:
                return False
            if version.major == self.max_version.major:
                if version.minor > self.max_version.minor:
                    return False
                if version.minor == self.max_version.minor:
                    if version.patch > self.max_version.patch:
                        return False
                    if version.patch == self.max_version.patch and not self.include_max:
                        return False

        return True

    def __str__(self) -> str:
        """Convert range to string.

        Returns:
            String representation of range
        """
        if not self.min_version and not self.max_version:
            return "*"

        result = ""
        if self.min_version:
            result += f"{'[' if self.include_min else '('}{self.min_version}"
        else:
            result += "(-∞"

        result += ", "

        if self.max_version:
            result += f"{self.max_version}{']' if self.include_max else ')'}"
        else:
            result += "+∞)"

        return result

    @classmethod
    def parse(cls, range_str: str) -> "VersionRange":
        """Parse version range string.

        Args:
            range_str: Range string (e.g. "[1.0.0, 2.0.0)")

        Returns:
            VersionRange object

        Raises:
            ValueError: If range string is invalid
        """
        if range_str == "*":
            return cls()

        if not (range_str.startswith("[") or range_str.startswith("(")) or not (
            range_str.endswith("]") or range_str.endswith(")")
        ):
            raise ValueError(f"Invalid range format: {range_str}")

        include_min = range_str.startswith("[")
        include_max = range_str.endswith("]")

        # Remove brackets
        range_str = range_str[1:-1]

        # Split by comma
        parts = [p.strip() for p in range_str.split(",")]
        if len(parts) != 2:
            raise ValueError(f"Invalid range format: {range_str}")

        # Parse versions
        min_version = None if parts[0] == "-∞" else Version.parse(parts[0])
        max_version = None if parts[1] == "+∞" else Version.parse(parts[1])

        return cls(
            min_version=min_version,
            max_version=max_version,
            include_min=include_min,
            include_max=include_max,
        )


class CompatibilityChecker:
    """Checker for version compatibility."""

    def __init__(self):
        """Initialize compatibility checker."""
        self._breaking_changes: dict[tuple[Version, Version], list[VersionChange]] = {}
        self._compatibility_matrix: dict[str, dict[str, bool]] = {}

    def check_compatibility(
        self, version1: Version, version2: Version, strict: bool = False
    ) -> bool:
        """Check if two versions are compatible."""
        try:
            # In strict mode, versions must be exactly equal
            if strict:
                return version1 == version2

            # By default, versions are compatible if they have the same major version
            # and version2 is not a pre-release version
            if version1.major != version2.major:
                return False

            # Pre-release versions are only compatible with themselves
            if version1.pre_release or version2.pre_release:
                return version1 == version2

            return True
        except Exception as e:
            raise VersionCompatibilityError(version1, version2, str(e))

    def register_breaking_change(
        self, from_version: Version, to_version: Version, change: VersionChange
    ) -> None:
        """Register a breaking change between versions."""
        if (from_version, to_version) not in self._breaking_changes:
            self._breaking_changes[from_version, to_version] = []
        self._breaking_changes[from_version, to_version].append(change)

    def get_breaking_changes(
        self, from_version: Version, to_version: Version
    ) -> list[VersionChange]:
        """Get breaking changes between versions."""
        return self._breaking_changes.get((from_version, to_version), [])

    def set_compatibility(self, version1: str, version2: str, compatible: bool) -> None:
        """Set compatibility between two version strings."""
        if version1 not in self._compatibility_matrix:
            self._compatibility_matrix[version1] = {}
        self._compatibility_matrix[version1][version2] = compatible

        # Ensure symmetry
        if version2 not in self._compatibility_matrix:
            self._compatibility_matrix[version2] = {}
        self._compatibility_matrix[version2][version1] = compatible

    def is_compatible(self, version1: str, version2: str) -> bool | None:
        """Check if two version strings are marked as compatible."""
        if version1 in self._compatibility_matrix:
            return self._compatibility_matrix[version1].get(version2)
        return None

    def analyze_upgrade_path(
        self, from_version: Version, to_version: Version
    ) -> list[VersionChange]:
        """Analyze the upgrade path between versions."""
        changes: list[VersionChange] = []

        # Major version changes
        if to_version.major > from_version.major:
            changes.append(
                VersionChange(
                    type=VersionChangeType.MAJOR,
                    description=f"Major version upgrade from {from_version.major} to {to_version.major}",
                    breaking=True,
                )
            )

        # Minor version changes
        elif (
            to_version.major == from_version.major
            and to_version.minor > from_version.minor
        ):
            changes.append(
                VersionChange(
                    type=VersionChangeType.MINOR,
                    description=f"Minor version upgrade from {from_version.minor} to {to_version.minor}",
                    breaking=False,
                )
            )

        # Patch version changes
        elif (
            to_version.major == from_version.major
            and to_version.minor == from_version.minor
            and to_version.patch > from_version.patch
        ):
            changes.append(
                VersionChange(
                    type=VersionChangeType.PATCH,
                    description=f"Patch version upgrade from {from_version.patch} to {to_version.patch}",
                    breaking=False,
                )
            )

        # Pre-release changes
        if from_version.pre_release != to_version.pre_release:
            changes.append(
                VersionChange(
                    type=VersionChangeType.PRE_RELEASE,
                    description=f"Pre-release change from {from_version.pre_release or 'none'} to {to_version.pre_release or 'none'}",
                    breaking=False,
                )
            )

        # Add any registered breaking changes
        changes.extend(self.get_breaking_changes(from_version, to_version))

        return changes

    def to_dict(self) -> dict[str, Any]:
        """Convert compatibility checker state to dictionary."""
        return {
            "breaking_changes": {
                f"{k[0]}->{k[1]}": [
                    {
                        "type": c.type.name,
                        "description": c.description,
                        "breaking": c.breaking,
                        "affected_components": c.affected_components,
                    }
                    for c in v
                ]
                for k, v in self._breaking_changes.items()
            },
            "compatibility_matrix": self._compatibility_matrix,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompatibilityChecker":
        """Create compatibility checker from dictionary."""
        checker = cls()

        # Restore compatibility matrix
        checker._compatibility_matrix = data.get("compatibility_matrix", {})

        # Restore breaking changes
        for change_key, changes in data.get("breaking_changes", {}).items():
            from_str, to_str = change_key.split("->")
            from_version = Version.parse(from_str)  # type: ignore
            to_version = Version.parse(to_str)  # type: ignore
            checker._breaking_changes[from_version, to_version] = [
                VersionChange(
                    type=VersionChangeType[c["type"]],
                    description=c["description"],
                    breaking=c["breaking"],
                    affected_components=c["affected_components"],
                )
                for c in changes
            ]

        return checker
