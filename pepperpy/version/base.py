"""
Core version management functionality.
"""

import re
from typing import Any

from .errors import (
    VersionDependencyError,
    VersionParseError,
    VersionValidationError,
)
from .types import (
    Version,
    VersionChange,
    VersionDependency,
    VersionType,
)


class VersionManager:
    """Core version management functionality."""

    # Regex patterns for version parsing
    SEMVER_PATTERN = re.compile(
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<pre>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
        r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
    )

    def __init__(self):
        """Initialize version manager."""
        self._versions: dict[str, Version] = {}
        self._dependencies: dict[str, list[VersionDependency]] = {}
        self._changes: dict[tuple[Version, Version], list[VersionChange]] = {}

    def parse_version(
        self, version_str: str, version_type: VersionType = VersionType.SEMANTIC
    ) -> Version:
        """Parse a version string into a Version object."""
        if version_type == VersionType.SEMANTIC:
            match = self.SEMVER_PATTERN.match(version_str)
            if not match:
                raise VersionParseError(
                    version_str,
                    "Version string does not match semantic versioning format",
                )

            try:
                return Version(
                    major=int(match.group("major")),
                    minor=int(match.group("minor")),
                    patch=int(match.group("patch")),
                    pre_release=match.group("pre"),
                    build=match.group("build"),
                )
            except ValueError as e:
                raise VersionParseError(version_str, str(e))
        else:
            raise NotImplementedError(f"Version type {version_type} not supported")

    def register_version(self, component: str, version: Version) -> None:
        """Register a version for a component."""
        if not self._validate_version(version):
            raise VersionValidationError(version)
        self._versions[component] = version

    def get_version(self, component: str) -> Version | None:
        """Get the current version of a component."""
        return self._versions.get(component)

    def register_dependency(
        self, component: str, dependency: VersionDependency
    ) -> None:
        """Register a dependency for a component."""
        if component not in self._dependencies:
            self._dependencies[component] = []
        self._dependencies[component].append(dependency)

    def check_dependencies(self, component: str) -> bool:
        """Check if all dependencies for a component are satisfied."""
        if component not in self._dependencies:
            return True

        for dep in self._dependencies[component]:
            dep_version = self.get_version(dep.component)
            if dep_version is None:
                if dep.required:
                    raise VersionDependencyError(
                        dep.component, dep.version, "Required dependency not found"
                    )
                continue

            if not self._check_compatibility(dep_version, dep.version):
                raise VersionDependencyError(
                    dep.component,
                    dep.version,
                    f"Incompatible version {dep_version}",
                )

        return True

    def register_changes(
        self, from_version: Version, to_version: Version, changes: list[VersionChange]
    ) -> None:
        """Register changes between versions."""
        self._changes[from_version, to_version] = changes

    def get_changes(
        self, from_version: Version, to_version: Version
    ) -> list[VersionChange]:
        """Get changes between versions."""
        return self._changes.get((from_version, to_version), [])

    def _validate_version(self, version: Version) -> bool:
        """Validate a version object."""
        try:
            # Validate numeric components
            if any(x < 0 for x in [version.major, version.minor, version.patch]):
                return False

            # Validate pre-release format if present
            if version.pre_release and not re.match(
                r"^[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*$", version.pre_release
            ):
                return False

            # Validate build metadata format if present
            if version.build and not re.match(
                r"^[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*$", version.build
            ):
                return False

            return True
        except Exception:
            return False

    def _check_compatibility(self, version1: Version, version2: Version) -> bool:
        """Check if two versions are compatible."""
        # By default, versions are compatible if they have the same major version
        return version1.major == version2.major

    def to_dict(self) -> dict[str, Any]:
        """Convert version manager state to dictionary."""
        return {
            "versions": {k: str(v) for k, v in self._versions.items()},
            "dependencies": {
                k: [
                    {
                        "component": d.component,
                        "version": str(d.version),
                        "required": d.required,
                        "compatibility_range": (
                            (
                                str(d.compatibility_range[0]),
                                str(d.compatibility_range[1]),
                            )
                            if d.compatibility_range
                            else None
                        ),
                    }
                    for d in v
                ]
                for k, v in self._dependencies.items()
            },
            "changes": {
                f"{k[0]}->{k[1]}": [
                    {
                        "type": c.type.name,
                        "description": c.description,
                        "breaking": c.breaking,
                        "affected_components": c.affected_components,
                    }
                    for c in v
                ]
                for k, v in self._changes.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionManager":
        """Create version manager from dictionary."""
        manager = cls()

        # Restore versions
        for component, version_str in data.get("versions", {}).items():
            manager._versions[component] = manager.parse_version(version_str)

        # Restore dependencies
        for component, deps in data.get("dependencies", {}).items():
            manager._dependencies[component] = []
            for dep in deps:
                version = manager.parse_version(dep["version"])
                compatibility_range = None
                if dep.get("compatibility_range"):
                    compatibility_range = (
                        manager.parse_version(dep["compatibility_range"][0]),
                        manager.parse_version(dep["compatibility_range"][1]),
                    )
                manager._dependencies[component].append(
                    VersionDependency(
                        component=dep["component"],
                        version=version,
                        required=dep["required"],
                        compatibility_range=compatibility_range,
                    )
                )

        # Restore changes
        for change_key, changes in data.get("changes", {}).items():
            from_str, to_str = change_key.split("->")
            from_version = manager.parse_version(from_str)
            to_version = manager.parse_version(to_str)
            manager._changes[from_version, to_version] = [
                VersionChange(
                    type=c["type"],
                    description=c["description"],
                    breaking=c["breaking"],
                    affected_components=c["affected_components"],
                )
                for c in changes
            ]

        return manager
