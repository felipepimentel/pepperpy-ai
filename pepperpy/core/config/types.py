"""Type definitions for the configuration system."""

from typing import Any, Protocol, TypeVar

from pydantic import BaseModel


class ConfigWatcher(Protocol):
    """Protocol for configuration change watchers."""

    async def on_config_change(
        self, old_config: BaseModel, new_config: BaseModel
    ) -> None:
        """Handle configuration changes.

        Args:
            old_config: Previous configuration
            new_config: New configuration

        """
        ...


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            field: Optional field that failed validation
            value: Optional invalid value
            details: Optional additional details

        """
        super().__init__(message)
        self.field = field
        self.value = value
        self.details = details or {}


# Type variable for configuration models
ConfigT = TypeVar("ConfigT", bound=BaseModel)
