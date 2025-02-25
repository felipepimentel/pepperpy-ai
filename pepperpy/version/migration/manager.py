"""
Version migration management functionality.
"""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..errors import VersionMigrationError
from ..types import Version


@dataclass
class MigrationStep:
    """Represents a single migration step."""

    description: str
    upgrade_func: Callable[..., bool]
    rollback_func: Callable[..., bool]
    dependencies: list[str] = field(default_factory=list)
    validation_func: Callable[..., bool] | None = None


class MigrationManager:
    """Manager for version migrations."""

    def __init__(self):
        """Initialize migration manager."""
        self._migrations: dict[tuple[Version, Version], list[MigrationStep]] = {}
        self._executed_migrations: dict[str, list[tuple[Version, Version]]] = (
            defaultdict(list)
        )
        self._migration_history: list[dict[str, Any]] = []

    def register_migration(
        self,
        from_version: Version,
        to_version: Version,
        steps: list[MigrationStep],
    ) -> None:
        """Register migration steps between versions."""
        if (from_version, to_version) in self._migrations:
            raise VersionMigrationError(
                from_version,
                to_version,
                "Migration already registered for these versions",
            )

        self._migrations[from_version, to_version] = steps

    def get_migration_steps(
        self, from_version: Version, to_version: Version
    ) -> list[MigrationStep]:
        """Get migration steps between versions."""
        return self._migrations.get((from_version, to_version), [])

    def migrate(
        self,
        component: str,
        from_version: Version,
        to_version: Version,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Execute migration from one version to another."""
        if context is None:
            context = {}

        try:
            steps = self.get_migration_steps(from_version, to_version)
            if not steps:
                raise VersionMigrationError(
                    from_version,
                    to_version,
                    "No migration steps registered for these versions",
                )

            # Validate dependencies
            self._validate_dependencies(steps)

            # Execute each step
            for step in steps:
                if not self._execute_step(step, context):
                    raise VersionMigrationError(
                        from_version,
                        to_version,
                        f"Migration step failed: {step.description}",
                    )

            # Record successful migration
            self._record_migration(component, from_version, to_version, "upgrade", True)
            return True

        except Exception as e:
            self._record_migration(
                component, from_version, to_version, "upgrade", False, str(e)
            )
            raise

    def rollback(
        self,
        component: str,
        from_version: Version,
        to_version: Version,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Rollback migration from one version to another."""
        if context is None:
            context = {}

        try:
            steps = self.get_migration_steps(to_version, from_version)
            if not steps:
                raise VersionMigrationError(
                    from_version,
                    to_version,
                    "No rollback steps registered for these versions",
                )

            # Execute rollback steps in reverse order
            for step in reversed(steps):
                if not self._execute_rollback(step, context):
                    raise VersionMigrationError(
                        from_version,
                        to_version,
                        f"Rollback step failed: {step.description}",
                    )

            # Record successful rollback
            self._record_migration(
                component, from_version, to_version, "rollback", True
            )
            return True

        except Exception as e:
            self._record_migration(
                component, from_version, to_version, "rollback", False, str(e)
            )
            raise

    def get_migration_history(
        self, component: str | None = None
    ) -> list[dict[str, Any]]:
        """Get migration history for a component."""
        if component:
            return [
                entry
                for entry in self._migration_history
                if entry["component"] == component
            ]
        return self._migration_history

    def _validate_dependencies(self, steps: list[MigrationStep]) -> None:
        """Validate migration step dependencies."""
        available_steps = set()
        for step in steps:
            for dep in step.dependencies:
                if dep not in available_steps:
                    raise VersionMigrationError(
                        None,  # type: ignore
                        None,  # type: ignore
                        f"Dependency '{dep}' not satisfied for step: {step.description}",
                    )
            available_steps.add(step.description)

    def _execute_step(self, step: MigrationStep, context: dict[str, Any]) -> bool:
        """Execute a migration step."""
        try:
            # Run validation if available
            if step.validation_func and not step.validation_func(context):
                raise VersionMigrationError(
                    None,  # type: ignore
                    None,  # type: ignore
                    f"Validation failed for step: {step.description}",
                )

            # Execute the upgrade
            return step.upgrade_func(context)
        except Exception as e:
            raise VersionMigrationError(
                None,  # type: ignore
                None,  # type: ignore
                f"Step execution failed: {step.description} - {e!s}",
            )

    def _execute_rollback(self, step: MigrationStep, context: dict[str, Any]) -> bool:
        """Execute a rollback step."""
        try:
            return step.rollback_func(context)
        except Exception as e:
            raise VersionMigrationError(
                None,  # type: ignore
                None,  # type: ignore
                f"Rollback execution failed: {step.description} - {e!s}",
            )

    def _record_migration(
        self,
        component: str,
        from_version: Version,
        to_version: Version,
        operation: str,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Record a migration operation."""
        record = {
            "component": component,
            "from_version": str(from_version),
            "to_version": str(to_version),
            "operation": operation,
            "success": success,
            "timestamp": None,  # TODO: Add timestamp
            "error": error,
        }
        self._migration_history.append(record)

        if success:
            self._executed_migrations[component].append((from_version, to_version))

    def to_dict(self) -> dict[str, Any]:
        """Convert migration manager state to dictionary."""
        return {
            "migrations": {
                f"{k[0]}->{k[1]}": [
                    {
                        "description": step.description,
                        "dependencies": step.dependencies,
                    }
                    for step in steps
                ]
                for k, steps in self._migrations.items()
            },
            "executed_migrations": {
                component: [
                    f"{from_version}->{to_version}"
                    for from_version, to_version in migrations
                ]
                for component, migrations in self._executed_migrations.items()
            },
            "migration_history": self._migration_history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MigrationManager":
        """Create migration manager from dictionary."""
        manager = cls()
        manager._migration_history = data.get("migration_history", [])

        # Note: We can't restore the actual migration steps since they contain
        # callable functions. We only restore the metadata and history.

        return manager
