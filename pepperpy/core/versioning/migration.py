"""
Migration management functionality.
"""

import datetime
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from pepperpy.core.versioning.semver import SemVer, Version, VersionComponent


class VersionMigrationError(Exception):
    """Exception raised for version migration errors."""

    def __init__(
        self,
        from_version: Optional[Version] = None,
        to_version: Optional[Version] = None,
        message: Optional[str] = None,
    ):
        """Initialize with versions and message."""
        self.from_version = from_version
        self.to_version = to_version
        self.message = message
        super().__init__(
            f"Migration failed: {from_version} -> {to_version} - {message}"
            if from_version and to_version and message
            else "Migration failed"
        )


class MigrationManager:
    """Manages version migrations."""

    def __init__(self):
        """Initialize migration manager."""
        self._migrations: Dict[VersionComponent, Dict[str, List[MigrationStep]]] = {
            component: {} for component in VersionComponent
        }
        self._executed_migrations: Dict[VersionComponent, Dict[str, List[str]]] = {
            component: {} for component in VersionComponent
        }
        self._migration_history: List[Dict[str, Any]] = []
        self._logger = logging.getLogger(__name__)

    def register_migration(
        self,
        component: VersionComponent,
        from_version: Union[str, Version],
        to_version: Union[str, Version],
        step: "MigrationStep",
    ) -> None:
        """Register a migration step."""
        # Convert string versions to Version objects
        if isinstance(from_version, str):
            from_version = SemVer.parse(from_version)
        if isinstance(to_version, str):
            to_version = SemVer.parse(to_version)

        # Validate versions
        SemVer.validate(from_version)
        SemVer.validate(to_version)

        # Create migration key
        migration_key = f"{from_version}->{to_version}"

        # Initialize migration list if needed
        if migration_key not in self._migrations[component]:
            self._migrations[component][migration_key] = []

        # Add step to migration
        self._migrations[component][migration_key].append(step)

    def get_migration_steps(
        self,
        component: VersionComponent,
        from_version: Union[str, Version],
        to_version: Union[str, Version],
    ) -> List["MigrationStep"]:
        """Get migration steps for a specific version transition."""
        # Convert string versions to Version objects
        if isinstance(from_version, str):
            from_version = SemVer.parse(from_version)
        if isinstance(to_version, str):
            to_version = SemVer.parse(to_version)

        # Validate versions
        SemVer.validate(from_version)
        SemVer.validate(to_version)

        # Create migration key
        migration_key = f"{from_version}->{to_version}"

        # Return steps for the migration
        return self._migrations[component].get(migration_key, [])

    def execute_migration(
        self,
        component: VersionComponent,
        from_version: Union[str, Version],
        to_version: Union[str, Version],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Execute a migration."""
        # Convert string versions to Version objects
        if isinstance(from_version, str):
            from_version = SemVer.parse(from_version)
        if isinstance(to_version, str):
            to_version = SemVer.parse(to_version)

        # Validate versions
        SemVer.validate(from_version)
        SemVer.validate(to_version)

        # Create migration key
        migration_key = f"{from_version}->{to_version}"

        # Get steps for the migration
        steps = self.get_migration_steps(component, from_version, to_version)
        if not steps:
            self._logger.warning(
                f"No migration steps found for {component.value}: {migration_key}"
            )
            return False

        # Initialize context if not provided
        if context is None:
            context = {}

        # Add migration info to context
        context.update(
            {
                "component": component.value,
                "from_version": str(from_version),
                "to_version": str(to_version),
            }
        )

        # Execute each step
        success = True
        executed_steps = []
        for step in steps:
            try:
                self._logger.info(
                    f"Executing migration step: {step.description} for {migration_key}"
                )
                if step.execute(context):
                    executed_steps.append(step.description)
                else:
                    self._logger.warning(
                        f"Migration step failed: {step.description} for {migration_key}"
                    )
                    success = False
                    break
            except Exception as e:
                self._logger.error(
                    f"Error executing migration step: {step.description} for {migration_key} - {e}"
                )
                success = False
                break

        # Record migration execution
        self._record_migration(
            component, from_version, to_version, executed_steps, success
        )

        return success

    def rollback_migration(
        self,
        component: VersionComponent,
        from_version: Union[str, Version],
        to_version: Union[str, Version],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Rollback a migration."""
        # Convert string versions to Version objects
        if isinstance(from_version, str):
            from_version = SemVer.parse(from_version)
        if isinstance(to_version, str):
            to_version = SemVer.parse(to_version)

        # Validate versions
        SemVer.validate(from_version)
        SemVer.validate(to_version)

        # Create migration key
        migration_key = f"{from_version}->{to_version}"

        # Check if migration was executed
        if not self._was_migration_executed(component, from_version, to_version):
            self._logger.warning(
                f"Migration was not executed, cannot rollback: {component.value} {migration_key}"
            )
            return False

        # Get steps for the migration
        steps = self.get_migration_steps(component, from_version, to_version)
        if not steps:
            self._logger.warning(
                f"No migration steps found for rollback: {component.value} {migration_key}"
            )
            return False

        # Initialize context if not provided
        if context is None:
            context = {}

        # Add migration info to context
        context.update(
            {
                "component": component.value,
                "from_version": str(from_version),
                "to_version": str(to_version),
                "operation": "rollback",
            }
        )

        # Execute each step in reverse order
        success = True
        rolled_back_steps = []
        for step in reversed(steps):
            try:
                self._logger.info(
                    f"Rolling back migration step: {step.description} for {migration_key}"
                )
                if step.execute(context, operation="rollback"):
                    rolled_back_steps.append(step.description)
                else:
                    self._logger.warning(
                        f"Rollback step failed: {step.description} for {migration_key}"
                    )
                    success = False
                    break
            except Exception as e:
                self._logger.error(
                    f"Error rolling back migration step: {step.description} for {migration_key} - {e}"
                )
                success = False
                break

        # Record rollback execution
        if success:
            self._remove_migration_record(component, from_version, to_version)

        return success

    def _record_migration(
        self,
        component: VersionComponent,
        from_version: Version,
        to_version: Version,
        executed_steps: List[str],
        success: bool,
    ) -> None:
        """Record a migration execution."""
        # Create migration key
        migration_key = f"{from_version}->{to_version}"

        # Initialize component migrations if needed
        if component not in self._executed_migrations:
            self._executed_migrations[component] = {}

        # Initialize migration list if needed
        if migration_key not in self._executed_migrations[component]:
            self._executed_migrations[component][migration_key] = []

        # Add executed steps
        self._executed_migrations[component][migration_key].extend(executed_steps)

        # Add to history
        self._migration_history.append(
            {
                "component": component.value,
                "from_version": str(from_version),
                "to_version": str(to_version),
                "steps": executed_steps,
                "success": success,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _remove_migration_record(
        self, component: VersionComponent, from_version: Version, to_version: Version
    ) -> None:
        """Remove a migration execution record."""
        # Create migration key
        migration_key = f"{from_version}->{to_version}"

        # Remove from executed migrations
        if (
            component in self._executed_migrations
            and migration_key in self._executed_migrations[component]
        ):
            del self._executed_migrations[component][migration_key]

    def _was_migration_executed(
        self, component: VersionComponent, from_version: Version, to_version: Version
    ) -> bool:
        """Check if a migration was executed."""
        # Create migration key
        migration_key = f"{from_version}->{to_version}"

        # Check if migration was executed
        return (
            component in self._executed_migrations
            and migration_key in self._executed_migrations[component]
            and self._executed_migrations[component][migration_key]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "executed_migrations": {
                component.value: {
                    migration_key: [
                        f"{from_version}->{to_version}"
                        for from_version, to_version in migrations
                    ]
                    for migration_key, migrations in component_migrations.items()
                }
                for component, component_migrations in self._executed_migrations.items()
            },
            "migration_history": self._migration_history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MigrationManager":
        """Create migration manager from dictionary."""
        manager = cls()
        
        # Load executed migrations
        executed_migrations = data.get("executed_migrations", {})
        for component_str, migrations in executed_migrations.items():
            component = VersionComponent(component_str)
            for migration_key, steps in migrations.items():
                manager._executed_migrations[component][migration_key] = steps
        
        # Load migration history
        manager._migration_history = data.get("migration_history", [])
        
        return manager


"""
Migration step functionality.
"""


class MigrationStepBuilder:
    """Builder for migration steps."""

    def __init__(self, description: str):
        """Initialize with description."""
        self.description = description
        self.dependencies: Set[str] = set()
        self.upgrade_func: Optional[Callable[[Dict[str, Any]], bool]] = None
        self.rollback_func: Optional[Callable[[Dict[str, Any]], bool]] = None
        self.validation_func: Optional[Callable[[Dict[str, Any]], bool]] = None
        self.error_handlers: Dict[Type[Exception], Callable[[Exception], None]] = {}

    def depends_on(self, dependency: str) -> "MigrationStepBuilder":
        """Add a dependency."""
        self.dependencies.add(dependency)
        return self

    def upgrade(
        self, func: Callable[[Dict[str, Any]], bool]
    ) -> "MigrationStepBuilder":
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

        return MigrationStep(
            description=self.description,
            dependencies=self.dependencies,
            upgrade_func=self._wrap_upgrade_func(),
            rollback_func=self.rollback_func,
            validation_func=self.validation_func,
            error_handlers=self.error_handlers,
        )

    def _wrap_upgrade_func(self) -> Callable[[Dict[str, Any]], bool]:
        """Wrap the upgrade function with error handling."""
        upgrade_func = self.upgrade_func

        def wrapped(context: Dict[str, Any]) -> bool:
            try:
                return upgrade_func(context)
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
    dependencies: Set[str] = field(default_factory=set)
    upgrade_func: Callable[[Dict[str, Any]], bool] = field(default_factory=lambda: lambda _: True)
    rollback_func: Optional[Callable[[Dict[str, Any]], bool]] = None
    validation_func: Optional[Callable[[Dict[str, Any]], bool]] = None
    error_handlers: Dict[Type[Exception], Callable[[Exception], None]] = field(
        default_factory=dict
    )

    def execute(self, context: Dict[str, Any], operation: str = "upgrade") -> bool:
        """Execute the migration step."""
        try:
            # Validate if needed
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
                if self.rollback_func:
                    return self.rollback_func(context)
                else:
                    raise ValueError("No rollback function defined")
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

    return (
        create_step(description)
        .upgrade(upgrade)
        .rollback(rollback)
        .build()
    )


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
