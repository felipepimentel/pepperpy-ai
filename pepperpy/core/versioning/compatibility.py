"""
Version compatibility checking functionality.
"""

from typing import Any

from ..errors import VersionCompatibilityError
from ..types import Version, VersionChange, VersionChangeType


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
"""
Version compatibility checking support.
"""

from .checker import CompatibilityChecker
from .matrix import CompatibilityMatrix

__all__ = ["CompatibilityChecker", "CompatibilityMatrix"]
"""
Version compatibility matrix functionality.
"""

from collections import defaultdict
from typing import Any

from ..types import Version


class CompatibilityMatrix:
    """Matrix for tracking version compatibility."""

    def __init__(self):
        """Initialize compatibility matrix."""
        self._matrix: dict[str, dict[str, bool]] = {}
        self._components: dict[str, set[Version]] = defaultdict(set)
        self._compatibility_rules: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add_version(self, component: str, version: Version) -> None:
        """Add a version for a component to the matrix."""
        self._components[component].add(version)

    def set_compatibility(
        self,
        component1: str,
        version1: Version,
        component2: str,
        version2: Version,
        compatible: bool,
    ) -> None:
        """Set compatibility between two component versions."""
        key1 = f"{component1}@{version1}"
        key2 = f"{component2}@{version2}"

        if key1 not in self._matrix:
            self._matrix[key1] = {}
        if key2 not in self._matrix:
            self._matrix[key2] = {}

        self._matrix[key1][key2] = compatible
        self._matrix[key2][key1] = compatible  # Ensure symmetry

    def is_compatible(
        self, component1: str, version1: Version, component2: str, version2: Version
    ) -> bool | None:
        """Check if two component versions are compatible."""
        key1 = f"{component1}@{version1}"
        key2 = f"{component2}@{version2}"

        if key1 in self._matrix and key2 in self._matrix[key1]:
            return self._matrix[key1][key2]
        return None

    def add_compatibility_rule(
        self,
        component: str,
        rule: dict[str, Any],
    ) -> None:
        """Add a compatibility rule for a component."""
        self._compatibility_rules[component].append(rule)

    def check_compatibility_rules(self, component: str, version: Version) -> list[str]:
        """Check compatibility rules for a component version."""
        violations = []
        rules = self._compatibility_rules.get(component, [])

        for rule in rules:
            try:
                if not self._check_rule(component, version, rule):
                    violations.append(
                        f"Version {version} of {component} violates rule: {rule['description']}"
                    )
            except Exception as e:
                violations.append(f"Error checking rule: {e!s}")

        return violations

    def get_compatible_versions(
        self, component: str, version: Version
    ) -> dict[str, list[Version]]:
        """Get all compatible versions for a given component version."""
        compatible_versions: dict[str, list[Version]] = defaultdict(list)
        key = f"{component}@{version}"

        if key not in self._matrix:
            return dict(compatible_versions)

        for other_key, compatible in self._matrix[key].items():
            if compatible:
                other_component, other_version_str = other_key.split("@")
                other_version = Version.parse(other_version_str)  # type: ignore
                compatible_versions[other_component].append(other_version)

        return dict(compatible_versions)

    def get_incompatible_versions(
        self, component: str, version: Version
    ) -> dict[str, list[Version]]:
        """Get all incompatible versions for a given component version."""
        incompatible_versions: dict[str, list[Version]] = defaultdict(list)
        key = f"{component}@{version}"

        if key not in self._matrix:
            return dict(incompatible_versions)

        for other_key, compatible in self._matrix[key].items():
            if not compatible:
                other_component, other_version_str = other_key.split("@")
                other_version = Version.parse(other_version_str)  # type: ignore
                incompatible_versions[other_component].append(other_version)

        return dict(incompatible_versions)

    def _check_rule(
        self, component: str, version: Version, rule: dict[str, Any]
    ) -> bool:
        """Check if a version satisfies a compatibility rule."""
        rule_type = rule.get("type")
        if not rule_type:
            raise ValueError("Rule must have a type")

        if rule_type == "version_range":
            min_version = Version.parse(rule["min_version"])  # type: ignore
            max_version = Version.parse(rule["max_version"])  # type: ignore
            return min_version <= version <= max_version

        elif rule_type == "dependency":
            dep_component = rule["component"]
            dep_version = Version.parse(rule["version"])  # type: ignore
            compatibility = self.is_compatible(
                component, version, dep_component, dep_version
            )
            return compatibility if compatibility is not None else False

        elif rule_type == "custom":
            # Custom rules should provide a validation function
            validator = rule.get("validator")
            if not validator or not callable(validator):
                raise ValueError("Custom rule must provide a callable validator")
            return validator(component, version)

        else:
            raise ValueError(f"Unknown rule type: {rule_type}")

    def to_dict(self) -> dict[str, Any]:
        """Convert compatibility matrix state to dictionary."""
        return {
            "matrix": self._matrix,
            "components": {
                component: [str(v) for v in versions]
                for component, versions in self._components.items()
            },
            "compatibility_rules": self._compatibility_rules,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompatibilityMatrix":
        """Create compatibility matrix from dictionary."""
        matrix = cls()
        matrix._matrix = data.get("matrix", {})
        matrix._compatibility_rules = data.get("compatibility_rules", {})

        # Restore components and their versions
        for component, version_strs in data.get("components", {}).items():
            for version_str in version_strs:
                version = Version.parse(version_str)  # type: ignore
                matrix.add_version(component, version)

        return matrix

    def validate(self) -> list[str]:
        """Validate the entire compatibility matrix."""
        errors = []

        # Check for symmetry
        for key1 in self._matrix:
            for key2, compatible in self._matrix[key1].items():
                if key2 not in self._matrix:
                    errors.append(f"Missing reciprocal entry for {key2}")
                elif key1 not in self._matrix[key2]:
                    errors.append(
                        f"Missing reciprocal compatibility for {key1} -> {key2}"
                    )
                elif self._matrix[key2][key1] != compatible:
                    errors.append(
                        f"Inconsistent compatibility between {key1} and {key2}"
                    )

        # Check all components and versions against rules
        for component, versions in self._components.items():
            for version in versions:
                violations = self.check_compatibility_rules(component, version)
                errors.extend(violations)

        return errors
