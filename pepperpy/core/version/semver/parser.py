"""
Semantic versioning parser functionality.
"""

import re

from ..errors import VersionParseError
from ..types import Version


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
    def parse_range(cls, range_str: str) -> tuple[Version, Version]:
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
        pre_release: str | None = None,
        build: str | None = None,
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
        cls, version: Version, component: str, pre_release: str | None = None
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
