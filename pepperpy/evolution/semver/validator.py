"""
Semantic versioning validation functionality.
"""

import re
from typing import List, Optional

from ..types import Version, VersionComponent
from ..errors import VersionValidationError


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
        """Validate pre-release version."""
        if not version.pre_release:
            return True

        try:
            identifiers = version.pre_release.split(".")
            cls._validate_pre_release_identifiers(version.pre_release)

            if allowed_identifiers:
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
            raise VersionValidationError(version, str(e))

    @classmethod
    def _validate_pre_release_identifiers(cls, pre_release: str) -> None:
        """Validate individual pre-release identifiers."""
        identifiers = pre_release.split(".")
        for identifier in identifiers:
            # Numeric identifiers cannot have leading zeros
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
``` 