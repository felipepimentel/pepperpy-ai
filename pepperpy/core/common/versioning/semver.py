"""Semantic versioning implementation.

This module provides a comprehensive implementation of Semantic Versioning (SemVer):

- SemVer parsing and formatting
- Version comparison and validation
- Version increment and manipulation
- Pre-release and build metadata support
- Version range specification

The semantic versioning implementation follows the SemVer 2.0.0 specification
(https://semver.org/), ensuring consistent version handling across the framework.
"""

import re
from typing import List, Optional, Tuple

from ..errors import VersionParseError, VersionValidationError
from ..types import Version, VersionComponent


class SemVerParser:
    """Parser for semantic versioning."""

    # Regex pattern for semantic versioning
    SEMVER_PATTERN = re.compile(
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<pre>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
        r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
    )

    # Regex pattern for pre-release and build metadata identifiers
    IDENTIFIER_PATTERN = re.compile(r"^[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*$")

    @classmethod
    def parse(cls, version_str: str) -> Version:
        """Parse a version string into a Version object."""
        match = cls.SEMVER_PATTERN.match(version_str)
        if not match:
            raise VersionParseError(
                version_str, "Version string does not match semantic versioning format"
            )

        try:
            major = int(match.group("major"))
            minor = int(match.group("minor"))
            patch = int(match.group("patch"))
            pre_release = match.group("pre")
            build = match.group("build")

            # Validate pre-release and build metadata if present
            if pre_release and not cls.IDENTIFIER_PATTERN.match(pre_release):
                raise VersionParseError(
                    version_str, "Invalid pre-release identifier format"
                )
            if build and not cls.IDENTIFIER_PATTERN.match(build):
                raise VersionParseError(version_str, "Invalid build metadata format")

            return Version(
                major=major,
                minor=minor,
                patch=patch,
                pre_release=pre_release,
                build=build,
            )
        except ValueError as e:
            raise VersionParseError(version_str, str(e))

    @classmethod
    def parse_range(cls, range_str: str) -> Tuple[Version, Version]:
        """Parse a version range string into a tuple of Version objects."""
        parts = range_str.split("-")
        if len(parts) != 2:
            raise VersionParseError(
                range_str, "Version range must be in format 'version1-version2'"
            )

        try:
            version1 = cls.parse(parts[0].strip())
            version2 = cls.parse(parts[1].strip())
            return version1, version2
        except VersionParseError as e:
            raise VersionParseError(range_str, f"Invalid version in range: {e}")

    @classmethod
    def format(
        cls,
        major: int,
        minor: int,
        patch: int,
        pre_release: Optional[str] = None,
        build: Optional[str] = None,
    ) -> str:
        """Format version components into a version string."""
        version = f"{major}.{minor}.{patch}"
        if pre_release:
            if not cls.IDENTIFIER_PATTERN.match(pre_release):
                raise VersionParseError(
                    pre_release, "Invalid pre-release identifier format"
                )
            version += f"-{pre_release}"
        if build:
            if not cls.IDENTIFIER_PATTERN.match(build):
                raise VersionParseError(build, "Invalid build metadata format")
            version += f"+{build}"
        return version

    @classmethod
    def increment(
        cls, version: Version, component: str, pre_release: Optional[str] = None
    ) -> Version:
        """Create a new version by incrementing a component."""
        if component not in ["major", "minor", "patch"]:
            raise ValueError("Component must be one of: 'major', 'minor', 'patch'")

        major = version.major
        minor = version.minor
        patch = version.patch

        if component == "major":
            major += 1
            minor = 0
            patch = 0
        elif component == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        return Version(
            major=major,
            minor=minor,
            patch=patch,
            pre_release=pre_release,
            build=None,  # Build metadata is dropped on increment
        )


class SemVerValidator:
    """Validator for semantic versioning."""

    # Regex pattern for pre-release and build metadata identifiers
    IDENTIFIER_PATTERN = re.compile(r"^[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*$")

    # Dummy version for validation errors that don't need a specific version
    DUMMY_VERSION = Version(0, 0, 0)

    @classmethod
    def validate(cls, version: Version) -> bool:
        """Validate a version object according to semantic versioning rules."""
        try:
            # Validate numeric components
            if any(x < 0 for x in [version.major, version.minor, version.patch]):
                raise VersionValidationError(
                    version, "Version components cannot be negative"
                )

            # Validate pre-release format if present
            if version.pre_release:
                if not cls.IDENTIFIER_PATTERN.match(version.pre_release):
                    raise VersionValidationError(
                        version, "Invalid pre-release identifier format"
                    )
                cls._validate_pre_release_identifiers(version.pre_release)

            # Validate build metadata format if present
            if version.build:
                if not cls.IDENTIFIER_PATTERN.match(version.build):
                    raise VersionValidationError(
                        version, "Invalid build metadata format"
                    )
                cls._validate_build_identifiers(version.build)

            return True
        except VersionValidationError:
            raise
        except Exception as e:
            raise VersionValidationError(version, str(e))

    @classmethod
    def validate_increment(
        cls, current: Version, next_version: Version, component: VersionComponent
    ) -> bool:
        """Validate that a version increment is valid."""
        try:
            if component == VersionComponent.MAJOR:
                if next_version.major != current.major + 1:
                    raise VersionValidationError(
                        next_version,
                        "Major version must increment by 1",
                    )
                if next_version.minor != 0 or next_version.patch != 0:
                    raise VersionValidationError(
                        next_version,
                        "Minor and patch must be reset to 0 on major increment",
                    )

            elif component == VersionComponent.MINOR:
                if next_version.major != current.major:
                    raise VersionValidationError(
                        next_version,
                        "Major version must not change on minor increment",
                    )
                if next_version.minor != current.minor + 1:
                    raise VersionValidationError(
                        next_version,
                        "Minor version must increment by 1",
                    )
                if next_version.patch != 0:
                    raise VersionValidationError(
                        next_version,
                        "Patch must be reset to 0 on minor increment",
                    )

            elif component == VersionComponent.PATCH:
                if next_version.major != current.major:
                    raise VersionValidationError(
                        next_version,
                        "Major version must not change on patch increment",
                    )
                if next_version.minor != current.minor:
                    raise VersionValidationError(
                        next_version,
                        "Minor version must not change on patch increment",
                    )
                if next_version.patch != current.patch + 1:
                    raise VersionValidationError(
                        next_version,
                        "Patch version must increment by 1",
                    )

            return True
        except VersionValidationError:
            raise
        except Exception as e:
            raise VersionValidationError(next_version, str(e))

    @classmethod
    def validate_pre_release(
        cls, version: Version, allowed_identifiers: Optional[List[str]] = None
    ) -> bool:
        """Validate pre-release identifiers."""
        if not version.pre_release:
            return True

        try:
            cls._validate_pre_release_identifiers(version.pre_release)

            # Check against allowed identifiers if provided
            if allowed_identifiers:
                if version.pre_release not in allowed_identifiers:
                    raise VersionValidationError(
                        version,
                        f"Pre-release identifier '{version.pre_release}' not in allowed list: {allowed_identifiers}",
                    )

            return True
        except VersionValidationError:
            raise
        except Exception as e:
            raise VersionValidationError(version, str(e))

    @classmethod
    def _validate_pre_release_identifiers(cls, pre_release: str) -> None:
        """Validate individual pre-release identifiers."""
        for identifier in pre_release.split("."):
            if not identifier:
                raise ValueError("Pre-release identifiers cannot be empty")
            # Numeric identifiers cannot have leading zeros
            if identifier.isdigit() and len(identifier) > 1 and identifier[0] == "0":
                raise ValueError(
                    "Numeric pre-release identifiers cannot have leading zeros"
                )

    @classmethod
    def _validate_build_identifiers(cls, build: str) -> None:
        """Validate individual build metadata identifiers."""
        for identifier in build.split("."):
            if not identifier:
                raise ValueError("Build metadata identifiers cannot be empty")


def compare_versions(version1: Version, version2: Version) -> int:
    """Compare two versions according to semantic versioning rules.

    Returns:
        -1 if version1 < version2
        0 if version1 == version2
        1 if version1 > version2
    """
    # Compare major.minor.patch
    for v1, v2 in zip(
        [version1.major, version1.minor, version1.patch],
        [version2.major, version2.minor, version2.patch],
    ):
        if v1 < v2:
            return -1
        if v1 > v2:
            return 1

    # If we get here, major.minor.patch are equal

    # A version with pre-release is lower than one without
    if version1.pre_release is None and version2.pre_release is not None:
        return 1
    if version1.pre_release is not None and version2.pre_release is None:
        return -1
    if version1.pre_release is None and version2.pre_release is None:
        return 0  # Both versions are equal (build metadata doesn't affect precedence)

    # Compare pre-release identifiers
    # At this point, we know both pre_release values are not None
    assert version1.pre_release is not None  # for type checking
    assert version2.pre_release is not None  # for type checking

    pre1 = version1.pre_release.split(".")
    pre2 = version2.pre_release.split(".")

    for i in range(min(len(pre1), len(pre2))):
        # Numeric identifiers are compared numerically
        if pre1[i].isdigit() and pre2[i].isdigit():
            num1 = int(pre1[i])
            num2 = int(pre2[i])
            if num1 < num2:
                return -1
            if num1 > num2:
                return 1
        # Numeric identifiers have lower precedence than non-numeric
        elif pre1[i].isdigit() and not pre2[i].isdigit():
            return -1
        elif not pre1[i].isdigit() and pre2[i].isdigit():
            return 1
        # Non-numeric identifiers are compared lexically
        else:
            if pre1[i] < pre2[i]:
                return -1
            if pre1[i] > pre2[i]:
                return 1

    # If we get here, all common identifiers are equal
    # The one with fewer identifiers has higher precedence
    if len(pre1) < len(pre2):
        return -1
    if len(pre1) > len(pre2):
        return 1

    # If we get here, the versions are equal
    return 0


def parse_version(version_str: str) -> Version:
    """Parse a version string into a Version object."""
    return SemVerParser.parse(version_str)


# Alias for backward compatibility
SemVer = Version
