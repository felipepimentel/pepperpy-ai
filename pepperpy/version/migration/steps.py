"""
Migration step functionality.
"""

from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass, field

from ..types import Version
from ..errors import VersionMigrationError


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