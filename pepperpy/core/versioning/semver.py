from enum import Enum
from typing import List, Optional, Union


class VersionComponent(Enum):
    """Version component enum."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRE_RELEASE = "pre_release"
    BUILD = "build"


class VersionValidationError(Exception):
    """Exception raised for version validation errors."""

    def __init__(self, version=None, message=None):
        """Initialize with version and message."""
        self.version = version
        self.message = message
        super().__init__(f"Invalid version: {version} - {message}" if version and message else "Invalid version")


class Version:
    """Semantic version representation."""

    def __init__(
        self,
        major: int,
        minor: int,
        patch: int,
        pre_release: Optional[str] = None,
        build: Optional[str] = None,
    ):
        """Initialize version with components."""
        self.major = major
        self.minor = minor
        self.patch = patch
        self.pre_release = pre_release
        self.build = build

    def __str__(self) -> str:
        """Convert to string representation."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            version += f"-{self.pre_release}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Version({self.major}, {self.minor}, {self.patch}, '{self.pre_release}', '{self.build}')"

    def __eq__(self, other) -> bool:
        """Check equality with another version."""
        if not isinstance(other, Version):
            return False
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.pre_release == other.pre_release
            and self.build == other.build
        )

    def __lt__(self, other) -> bool:
        """Compare with another version."""
        if not isinstance(other, Version):
            return NotImplemented

        # Compare major, minor, patch
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch

        # Pre-release versions are lower than release versions
        if self.pre_release and not other.pre_release:
            return True
        if not self.pre_release and other.pre_release:
            return False

        # Compare pre-release identifiers
        if self.pre_release and other.pre_release:
            self_identifiers = self.pre_release.split(".")
            other_identifiers = other.pre_release.split(".")

            for i in range(min(len(self_identifiers), len(other_identifiers))):
                self_id = self_identifiers[i]
                other_id = other_identifiers[i]

                self_is_numeric = self_id.isdigit()
                other_is_numeric = other_id.isdigit()

                if self_is_numeric and other_is_numeric:
                    if int(self_id) != int(other_id):
                        return int(self_id) < int(other_id)
                elif self_is_numeric:
                    return True
                elif other_is_numeric:
                    return False
                elif self_id != other_id:
                    return self_id < other_id

            return len(self_identifiers) < len(other_identifiers)

        # Build metadata does not affect precedence
        return False


class SemVer:
    """Semantic versioning utility class."""

    VERSION_REGEX = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    DUMMY_VERSION = Version(0, 0, 0)

    @classmethod
    def parse(cls, version_str: str) -> Version:
        """Parse version string into Version object."""
        import re

        match = re.match(cls.VERSION_REGEX, version_str)
        if not match:
            raise VersionValidationError(version_str, "Invalid version format")

        major, minor, patch, pre_release, build = match.groups()

        try:
            major = int(major)
            minor = int(minor)
            patch = int(patch)
        except ValueError as e:
            raise VersionValidationError(version_str, f"Invalid version numbers: {e}") from e

        # Validate pre-release and build identifiers
        if pre_release:
            cls._validate_pre_release_identifiers(pre_release)

        if build:
            cls._validate_build_identifiers(build)

        return Version(major, minor, patch, pre_release, build)

    @classmethod
    def validate(cls, version: Union[str, Version]) -> bool:
        """Validate version string or object."""
        try:
            if isinstance(version, str):
                cls.parse(version)
            else:
                # Validate version object
                if not isinstance(version, Version):
                    raise VersionValidationError(version, "Not a Version object")

                if version.major < 0 or version.minor < 0 or version.patch < 0:
                    raise VersionValidationError(version, "Version components cannot be negative")

                if version.pre_release:
                    cls._validate_pre_release_identifiers(version.pre_release)

                if version.build:
                    cls._validate_build_identifiers(version.build)

            return True
        except VersionValidationError:
            raise
        except Exception as e:
            raise VersionValidationError(version, str(e)) from None

    @classmethod
    def validate_increment(
        cls, current: Version, next_version: Version, component: VersionComponent,
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
            raise VersionValidationError(next_version, str(e)) from None

    @classmethod
    def validate_pre_release(
        cls, version: Version, allowed_identifiers: Optional[List[str]] = None,
    ) -> bool:
        """Validate pre-release version."""
        if not version.pre_release:
            return True

        try:
            # Validate pre-release format
            cls._validate_pre_release_identifiers(version.pre_release)

            # Check if pre-release identifier is in allowed list
            if allowed_identifiers:
                identifiers = version.pre_release.split(".")
                if not any(
                    identifier in allowed_identifiers for identifier in identifiers
                ):
                    raise VersionValidationError(
                        version,
                        f"Pre-release identifier must be one of: {allowed_identifiers}",
                    )

            return True
        except VersionValidationError:
            raise
        except Exception as e:
            raise VersionValidationError(version, str(e)) from None

    @classmethod
    def _validate_pre_release_identifiers(cls, pre_release: str) -> None:
        """Validate individual pre-release identifiers."""
        identifiers = pre_release.split(".")

        for identifier in identifiers:
            if not identifier:
                raise VersionValidationError(
                    cls.DUMMY_VERSION,
                    "Pre-release identifiers cannot be empty",
                )

            if identifier.isdigit() and len(identifier) > 1 and identifier[0] == "0":
                raise VersionValidationError(
                    cls.DUMMY_VERSION,
                    f"Numeric pre-release identifier '{identifier}' cannot have leading zeros",
                )

    @classmethod
    def _validate_build_identifiers(cls, build: str) -> None:
        """Validate individual build metadata identifiers."""
        identifiers = build.split(".")

        for identifier in identifiers:
            if not identifier:
                raise VersionValidationError(
                    cls.DUMMY_VERSION,
                    "Build metadata identifiers cannot be empty",
                )
