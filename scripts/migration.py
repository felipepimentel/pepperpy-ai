#!/usr/bin/env python3
"""
PepperPy Framework Migration Tool
================================

This script provides tools for migrating between different versions of the PepperPy framework.
It helps with:
- Detecting breaking changes
- Updating import statements
- Migrating configuration files
- Applying code transformations

Usage:
    python migration.py check --from-version <version> --to-version <version> [--path <path>]
    python migration.py apply --from-version <version> --to-version <version> [--path <path>]
    python migration.py guide --from-version <version> --to-version <version>
"""

import argparse
import logging
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("pepperpy-migration")


class MigrationError(Exception):
    """Base exception for migration errors."""

    pass


class SemanticVersion:
    """Semantic version representation (MAJOR.MINOR.PATCH)."""

    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def parse(cls, version_str: str) -> "SemanticVersion":
        """Parse a version string into a SemanticVersion object."""
        try:
            major, minor, patch = map(int, version_str.split("."))
            return cls(major, minor, patch)
        except ValueError:
            raise ValueError(
                f"Invalid version format: {version_str}. Expected MAJOR.MINOR.PATCH"
            )

    def __lt__(self, other: "SemanticVersion") -> bool:
        """Compare versions."""
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch

    def __le__(self, other: "SemanticVersion") -> bool:
        """Less than or equal comparison."""
        return self < other or self == other

    def __gt__(self, other: "SemanticVersion") -> bool:
        """Greater than comparison."""
        return not (self < other or self == other)

    def __ge__(self, other: "SemanticVersion") -> bool:
        """Greater than or equal comparison."""
        return not self < other

    def __eq__(self, other: object) -> bool:
        """Check if versions are equal."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
        )

    def __str__(self) -> str:
        """Convert to string."""
        return f"{self.major}.{self.minor}.{self.patch}"


class DeprecationLevel(Enum):
    """Levels of deprecation for framework features."""

    WARNING = "warning"  # Still works, but emits a warning
    ERROR = "error"  # No longer works, raises an error
    REMOVED = "removed"  # Completely removed from the framework


class ImportChange:
    """Represents a change in import statements."""

    def __init__(
        self,
        old_import: str,
        new_import: str,
        version_introduced: str,
        deprecation_level: DeprecationLevel = DeprecationLevel.WARNING,
    ):
        self.old_import = old_import
        self.new_import = new_import
        self.version_introduced = version_introduced
        self.deprecation_level = deprecation_level


class APIChange:
    """Represents a change in the API."""

    def __init__(
        self,
        old_api: str,
        new_api: str,
        version_introduced: str,
        deprecation_level: DeprecationLevel = DeprecationLevel.WARNING,
    ):
        self.old_api = old_api
        self.new_api = new_api
        self.version_introduced = version_introduced
        self.deprecation_level = deprecation_level


# Define known import changes
IMPORT_CHANGES = [
    ImportChange(
        old_import=r"from pepperpy\.llm\.providers\.(.*) import (.*)",
        new_import=r"from pepperpy.providers.llm.\1 import \2",
        version_introduced="0.5.0",
        deprecation_level=DeprecationLevel.WARNING,
    ),
    ImportChange(
        old_import=r"from pepperpy\.storage\.(.*) import (.*)",
        new_import=r"from pepperpy.providers.storage.\1 import \2",
        version_introduced="0.5.0",
        deprecation_level=DeprecationLevel.WARNING,
    ),
    ImportChange(
        old_import=r"from pepperpy\.cloud\.(.*) import (.*)",
        new_import=r"from pepperpy.providers.cloud.\1 import \2",
        version_introduced="0.5.0",
        deprecation_level=DeprecationLevel.WARNING,
    ),
]

# Define known API changes
API_CHANGES = [
    APIChange(
        old_api=r"LLMProvider\(\)",
        new_api=r"LLMFactory.create()",
        version_introduced="0.5.0",
        deprecation_level=DeprecationLevel.WARNING,
    ),
    APIChange(
        old_api=r"StorageProvider\(\)",
        new_api=r"StorageFactory.create()",
        version_introduced="0.5.0",
        deprecation_level=DeprecationLevel.WARNING,
    ),
    APIChange(
        old_api=r"CloudProvider\(\)",
        new_api=r"CloudFactory.create()",
        version_introduced="0.5.0",
        deprecation_level=DeprecationLevel.WARNING,
    ),
]


class MigrationManager:
    """Manages the migration process between framework versions."""

    def __init__(self, from_version: str, to_version: str):
        """Initialize the migration manager."""
        self.from_version = SemanticVersion.parse(from_version)
        self.to_version = SemanticVersion.parse(to_version)

        if self.from_version >= self.to_version:
            raise MigrationError(
                f"From version ({from_version}) must be less than to version ({to_version})"
            )

    def check_compatibility(
        self, path: Union[str, Path]
    ) -> Dict[str, List[Tuple[str, int, str]]]:
        """
        Check for compatibility issues when migrating from one version to another.

        Args:
            path: Path to the directory to check

        Returns:
            Dictionary mapping file paths to lists of (issue, line number, suggestion) tuples
        """
        path = Path(path)
        if not path.exists():
            raise MigrationError(f"Path does not exist: {path}")

        issues = {}

        # Check for import changes
        import_issues = self._check_import_changes(path)
        if import_issues:
            issues.update(import_issues)

        # Check for API changes
        api_issues = self._check_api_changes(path)
        if api_issues:
            issues.update(api_issues)

        return issues

    def _check_import_changes(
        self, path: Path
    ) -> Dict[str, List[Tuple[str, int, str]]]:
        """Check for import changes."""
        issues = {}

        for file_path in path.glob("**/*.py"):
            file_issues = []

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                for change in IMPORT_CHANGES:
                    if re.search(change.old_import, line):
                        # Check if the change is relevant for the version range
                        change_version = SemanticVersion.parse(
                            change.version_introduced
                        )
                        if self.from_version < change_version <= self.to_version:
                            new_line = re.sub(
                                change.old_import, change.new_import, line
                            )
                            file_issues.append((
                                f"Import change: {line.strip()}",
                                i + 1,
                                f"Change to: {new_line.strip()}",
                            ))

            if file_issues:
                issues[str(file_path)] = file_issues

        return issues

    def _check_api_changes(self, path: Path) -> Dict[str, List[Tuple[str, int, str]]]:
        """Check for API changes."""
        issues = {}

        for file_path in path.glob("**/*.py"):
            file_issues = []

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                for change in API_CHANGES:
                    if re.search(change.old_api, line):
                        # Check if the change is relevant for the version range
                        change_version = SemanticVersion.parse(
                            change.version_introduced
                        )
                        if self.from_version < change_version <= self.to_version:
                            new_line = re.sub(change.old_api, change.new_api, line)
                            file_issues.append((
                                f"API change: {line.strip()}",
                                i + 1,
                                f"Change to: {new_line.strip()}",
                            ))

            if file_issues:
                issues[str(file_path)] = file_issues

        return issues

    def apply_migrations(
        self, path: Union[str, Path], dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Apply migrations to the codebase.

        Args:
            path: Path to the directory to migrate
            dry_run: If True, don't actually make changes

        Returns:
            Dictionary mapping file paths to the number of changes made
        """
        path = Path(path)
        if not path.exists():
            raise MigrationError(f"Path does not exist: {path}")

        changes_made = {}

        # Apply import changes
        import_changes = self._apply_import_changes(path, dry_run)
        if import_changes:
            changes_made.update(import_changes)

        # Apply API changes
        api_changes = self._apply_api_changes(path, dry_run)
        if api_changes:
            changes_made.update(api_changes)

        return changes_made

    def _apply_import_changes(self, path: Path, dry_run: bool) -> Dict[str, int]:
        """Apply import changes."""
        changes_made = {}

        for file_path in path.glob("**/*.py"):
            file_changes = 0

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            new_content = content

            for change in IMPORT_CHANGES:
                # Check if the change is relevant for the version range
                change_version = SemanticVersion.parse(change.version_introduced)
                if self.from_version < change_version <= self.to_version:
                    # Count occurrences before replacement
                    occurrences = len(re.findall(change.old_import, new_content))
                    file_changes += occurrences

                    # Apply the replacement
                    new_content = re.sub(
                        change.old_import, change.new_import, new_content
                    )

            if file_changes > 0 and not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                changes_made[str(file_path)] = file_changes
            elif file_changes > 0:
                changes_made[str(file_path)] = file_changes

        return changes_made

    def _apply_api_changes(self, path: Path, dry_run: bool) -> Dict[str, int]:
        """Apply API changes."""
        changes_made = {}

        for file_path in path.glob("**/*.py"):
            file_changes = 0

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            new_content = content

            for change in API_CHANGES:
                # Check if the change is relevant for the version range
                change_version = SemanticVersion.parse(change.version_introduced)
                if self.from_version < change_version <= self.to_version:
                    # Count occurrences before replacement
                    occurrences = len(re.findall(change.old_api, new_content))
                    file_changes += occurrences

                    # Apply the replacement
                    new_content = re.sub(change.old_api, change.new_api, new_content)

            if file_changes > 0 and not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                changes_made[str(file_path)] = file_changes
            elif file_changes > 0:
                changes_made[str(file_path)] = file_changes

        return changes_made

    def generate_migration_guide(self) -> str:
        """
        Generate a migration guide for the specified version range.

        Returns:
            A string containing the migration guide
        """
        guide = [
            f"# Migration Guide: {self.from_version} to {self.to_version}",
            "",
            "This guide helps you migrate your code from "
            f"PepperPy {self.from_version} to {self.to_version}.",
            "",
            "## Breaking Changes",
            "",
        ]

        # Add import changes
        import_changes = [
            change
            for change in IMPORT_CHANGES
            if self.from_version
            < SemanticVersion.parse(change.version_introduced)
            <= self.to_version
        ]

        if import_changes:
            guide.append("### Import Changes")
            guide.append("")

            for change in import_changes:
                guide.append(f"- Change `{change.old_import}` to `{change.new_import}`")

            guide.append("")

        # Add API changes
        api_changes = [
            change
            for change in API_CHANGES
            if self.from_version
            < SemanticVersion.parse(change.version_introduced)
            <= self.to_version
        ]

        if api_changes:
            guide.append("### API Changes")
            guide.append("")

            for change in api_changes:
                guide.append(f"- Change `{change.old_api}` to `{change.new_api}`")

            guide.append("")

        # Add version-specific notes
        guide.append("## Version-Specific Notes")
        guide.append("")

        # Add notes for each major version in the range
        for major in range(self.from_version.major, self.to_version.major + 1):
            guide.append(f"### Version {major}.x")
            guide.append("")
            guide.append(
                f"- See the [changelog](https://github.com/pepperpy/pepperpy/blob/main/CHANGELOG.md) for version {major}.x"
            )
            guide.append("")

        # Add migration tool instructions
        guide.append("## Using the Migration Tool")
        guide.append("")
        guide.append(
            "You can use the migration tool to automatically apply these changes:"
        )
        guide.append("")
        guide.append("```bash")
        guide.append(
            f"python -m scripts.migration apply --from-version {self.from_version} --to-version {self.to_version} --path /path/to/your/code"
        )
        guide.append("```")
        guide.append("")
        guide.append("To check for issues without making changes:")
        guide.append("")
        guide.append("```bash")
        guide.append(
            f"python -m scripts.migration check --from-version {self.from_version} --to-version {self.to_version} --path /path/to/your/code"
        )
        guide.append("```")

        return "\n".join(guide)


def main():
    """Main entry point for the migration tool."""
    parser = argparse.ArgumentParser(description="PepperPy Framework Migration Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check for compatibility issues")
    check_parser.add_argument("--from-version", required=True, help="Source version")
    check_parser.add_argument("--to-version", required=True, help="Target version")
    check_parser.add_argument(
        "--path", default=".", help="Path to the directory to check"
    )

    # Apply command
    apply_parser = subparsers.add_parser("apply", help="Apply migrations")
    apply_parser.add_argument("--from-version", required=True, help="Source version")
    apply_parser.add_argument("--to-version", required=True, help="Target version")
    apply_parser.add_argument(
        "--path", default=".", help="Path to the directory to migrate"
    )
    apply_parser.add_argument(
        "--dry-run", action="store_true", help="Don't actually make changes"
    )

    # Guide command
    guide_parser = subparsers.add_parser("guide", help="Generate a migration guide")
    guide_parser.add_argument("--from-version", required=True, help="Source version")
    guide_parser.add_argument("--to-version", required=True, help="Target version")
    guide_parser.add_argument("--output", help="Output file path (default: stdout)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        manager = MigrationManager(args.from_version, args.to_version)

        if args.command == "check":
            issues = manager.check_compatibility(args.path)

            if issues:
                print(
                    f"Found {sum(len(v) for v in issues.values())} issues in {len(issues)} files:"
                )
                print()

                for file_path, file_issues in issues.items():
                    print(f"{file_path}:")
                    for issue, line_num, suggestion in file_issues:
                        print(f"  Line {line_num}: {issue}")
                        print(f"    Suggestion: {suggestion}")
                    print()

                sys.exit(1)
            else:
                print("No compatibility issues found.")

        elif args.command == "apply":
            changes = manager.apply_migrations(args.path, args.dry_run)

            if changes:
                print(f"Made {sum(changes.values())} changes in {len(changes)} files:")
                print()

                for file_path, num_changes in changes.items():
                    print(f"{file_path}: {num_changes} changes")

                if args.dry_run:
                    print("\nThis was a dry run. No changes were actually made.")
            else:
                print("No changes needed.")

        elif args.command == "guide":
            guide = manager.generate_migration_guide()

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(guide)
                print(f"Migration guide written to {args.output}")
            else:
                print(guide)

    except MigrationError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception:
        logger.exception("An unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
