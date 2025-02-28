"""Version migration management system.

This module provides tools for managing migrations between different versions:

- MigrationManager: Core class for managing version migrations
- MigrationStep: Interface for individual migration steps
- MigrationContext: Context for executing migration steps
- Migration path planning and execution
- Validation steps for pre and post-migration checks

The migration system enables applications to safely upgrade between versions,
ensuring data consistency and proper handling of breaking changes.
"""

from .manager import MigrationManager
from .steps import (
    MigrationContext,
    MigrationStep,
    create_data_migration_step,
    create_step,
    create_validation_step,
)

__all__ = [
    "MigrationContext",
    "MigrationManager",
    "MigrationStep",
    "create_data_migration_step",
    "create_step",
    "create_validation_step",
]
"""
Version migration management functionality.
"""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

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


"""
Migration step functionality.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Type

from ..types import Version


@dataclass
class MigrationContext:
    """Context for migration operations."""

    component: str
    from_version: Version
    to_version: Version
    data: Dict[str, Any] = field(default_factory=dict)
    backup: Dict[str, Any] = field(default_factory=dict)


class MigrationStepBuilder:
    """Builder for creating migration steps."""

    def __init__(self, description: str):
        """Initialize step builder."""
        self.description = description
        self.dependencies: List[str] = []
        self.upgrade_func: Optional[Callable[[Dict[str, Any]], bool]] = None
        self.rollback_func: Optional[Callable[[Dict[str, Any]], bool]] = None
        self.validation_func: Optional[Callable[[Dict[str, Any]], bool]] = None
        self.error_handlers: Dict[Type[Exception], Callable[[Exception], None]] = {}

    def depends_on(self, *steps: str) -> "MigrationStepBuilder":
        """Add dependencies for this step."""
        self.dependencies.extend(steps)
        return self

    def upgrade(self, func: Callable[[Dict[str, Any]], bool]) -> "MigrationStepBuilder":
        """Set the upgrade function."""
        self.upgrade_func = func
        return self

    def rollback(
        self, func: Callable[[Dict[str, Any]], bool]
    ) -> "MigrationStepBuilder":
        """Set the rollback function."""
        self.rollback_func = func
        return self

    def validate(
        self, func: Callable[[Dict[str, Any]], bool]
    ) -> "MigrationStepBuilder":
        """Set the validation function."""
        self.validation_func = func
        return self

    def on_error(
        self,
        exception_type: Type[Exception],
        handler: Callable[[Exception], None],
    ) -> "MigrationStepBuilder":
        """Add an error handler."""
        self.error_handlers[exception_type] = handler
        return self

    def build(self) -> "MigrationStep":
        """Build the migration step."""
        if not self.upgrade_func:
            raise ValueError("Upgrade function is required")
        if not self.rollback_func:
            raise ValueError("Rollback function is required")

        return MigrationStep(
            description=self.description,
            dependencies=self.dependencies,
            upgrade_func=self._wrap_upgrade_func(),
            rollback_func=self._wrap_rollback_func(),
            validation_func=self.validation_func,
            error_handlers=self.error_handlers,
        )

    def _wrap_upgrade_func(self) -> Callable[[Dict[str, Any]], bool]:
        """Wrap the upgrade function with error handling."""
        upgrade_func = self.upgrade_func

        def wrapped(context: Dict[str, Any]) -> bool:
            try:
                if upgrade_func:
                    return upgrade_func(context)
                return False
            except Exception as e:
                handler = self._get_error_handler(type(e))
                if handler:
                    handler(e)
                raise

        return wrapped

    def _wrap_rollback_func(self) -> Callable[[Dict[str, Any]], bool]:
        """Wrap the rollback function with error handling."""
        rollback_func = self.rollback_func

        def wrapped(context: Dict[str, Any]) -> bool:
            try:
                if rollback_func:
                    return rollback_func(context)
                return False
            except Exception as e:
                handler = self._get_error_handler(type(e))
                if handler:
                    handler(e)
                raise

        return wrapped

    def _get_error_handler(
        self, exception_type: Type[Exception]
    ) -> Optional[Callable[[Exception], None]]:
        """Get the appropriate error handler for an exception type."""
        for exc_type, handler in self.error_handlers.items():
            if issubclass(exception_type, exc_type):
                return handler
        return None


@dataclass
class MigrationStep:
    """Represents a single migration step."""

    description: str
    dependencies: List[str]
    upgrade_func: Callable[[Dict[str, Any]], bool]
    rollback_func: Callable[[Dict[str, Any]], bool]
    validation_func: Optional[Callable[[Dict[str, Any]], bool]] = None
    error_handlers: Dict[Type[Exception], Callable[[Exception], None]] = field(
        default_factory=dict
    )

    def execute(self, context: Dict[str, Any], operation: str = "upgrade") -> bool:
        """Execute the migration step."""
        try:
            # Run validation if available
            if self.validation_func and not self.validation_func(context):
                raise VersionMigrationError(
                    None,  # type: ignore
                    None,  # type: ignore
                    f"Validation failed for step: {self.description}",
                )

            # Execute the operation
            if operation == "upgrade":
                return self.upgrade_func(context)
            elif operation == "rollback":
                return self.rollback_func(context)
            else:
                raise ValueError(f"Invalid operation: {operation}")

        except Exception as e:
            handler = self._get_error_handler(type(e))
            if handler:
                handler(e)
            raise

    def _get_error_handler(
        self, exception_type: Type[Exception]
    ) -> Optional[Callable[[Exception], None]]:
        """Get the appropriate error handler for an exception type."""
        for exc_type, handler in self.error_handlers.items():
            if issubclass(exception_type, exc_type):
                return handler
        return None


def create_step(description: str) -> MigrationStepBuilder:
    """Create a new migration step builder."""
    return MigrationStepBuilder(description)


def create_data_migration_step(
    description: str,
    upgrade_data: Dict[str, Any],
    rollback_data: Dict[str, Any],
) -> MigrationStep:
    """Create a simple data migration step."""

    def upgrade(context: Dict[str, Any]) -> bool:
        context.update(upgrade_data)
        return True

    def rollback(context: Dict[str, Any]) -> bool:
        context.update(rollback_data)
        return True

    return create_step(description).upgrade(upgrade).rollback(rollback).build()


def create_validation_step(
    description: str,
    validation_func: Callable[[Dict[str, Any]], bool],
) -> MigrationStep:
    """Create a validation-only step."""

    def noop(context: Dict[str, Any]) -> bool:
        return True

    return (
        create_step(description)
        .upgrade(noop)
        .rollback(noop)
        .validate(validation_func)
        .build()
    )


class MigrationPath:
    """Represents a path of migrations between versions."""

    def __init__(self, steps: List[Tuple[Version, Version]]) -> None:
        """Initialize migration path.

        Args:
            steps: List of migration steps (from_version, to_version)
        """
        self.steps = steps

    @property
    def from_version(self) -> Optional[Version]:
        """Get source version of migration path.

        Returns:
            Source version or None if path is empty
        """
        if not self.steps:
            return None
        return self.steps[0][0]

    @property
    def to_version(self) -> Optional[Version]:
        """Get target version of migration path.

        Returns:
            Target version or None if path is empty
        """
        if not self.steps:
            return None
        return self.steps[-1][1]

    @property
    def is_empty(self) -> bool:
        """Check if migration path is empty.

        Returns:
            True if path is empty, False otherwise
        """
        return len(self.steps) == 0

    def __len__(self) -> int:
        """Get number of steps in migration path.

        Returns:
            Number of steps
        """
        return len(self.steps)

    def __str__(self) -> str:
        """Get string representation of migration path.

        Returns:
            String representation
        """
        if not self.steps:
            return "Empty migration path"

        path_str = f"Migration path: {self.from_version} -> "
        for i, (_, to_ver) in enumerate(self.steps):
            if i < len(self.steps) - 1:
                path_str += f"{to_ver} -> "
            else:
                path_str += f"{to_ver}"

        return path_str

    def to_dict(self) -> Dict:
        """Convert migration path to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "steps": [
                {"from": str(from_ver), "to": str(to_ver)}
                for from_ver, to_ver in self.steps
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MigrationPath":
        """Create migration path from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            MigrationPath instance
        """
        steps = [
            (Version.parse(step["from"]), Version.parse(step["to"]))
            for step in data.get("steps", [])
        ]
        return cls(steps)


__all__ = ["MigrationManager", "MigrationPath"]
