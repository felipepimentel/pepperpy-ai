"""Resource type definitions."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class ResourceType(Enum):
    """Resource type enumeration."""

    STORAGE = auto()
    COMPUTE = auto()
    NETWORK = auto()
    MEMORY = auto()
    DATABASE = auto()


class ResourceState(Enum):
    """Resource state enumeration."""

    UNINITIALIZED = auto()
    INITIALIZING = auto()
    READY = auto()
    ERROR = auto()
    CLEANING = auto()
    CLEANED = auto()


class ResourceOperationError(Exception):
    """Base class for resource operation errors."""

    pass


class ResourceError(Exception):
    """Base class for resource errors."""

    def __init__(
        self,
        message: str,
        error_type: str,
        timestamp: float,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize resource error.

        Args:
            message: Error message
            error_type: Type of error
            timestamp: Error timestamp
            details: Optional error details

        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.timestamp = timestamp
        self.details = details or {}


ValidationFunc = Callable[[Dict[str, Any]], Optional[str]]


@dataclass
class ResourceConfig:
    """Resource configuration."""

    type: ResourceType
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: Optional[Dict[str, str]] = field(default=None)
    validators: List[ValidationFunc] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        self.validate()

    def add_validator(self, validator: ValidationFunc) -> None:
        """Add a validator function.

        Args:
            validator: Function that takes settings dict and returns error message if invalid.

        """
        self.validators.append(validator)

    def validate(self) -> None:
        """Validate settings using registered validators.

        Raises:
            ValueError: If validation fails.

        """
        for validator in self.validators:
            if error := validator(self.settings):
                raise ValueError(f"Validation failed: {error}")

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update settings and validate.

        Args:
            settings: New settings to update.

        Raises:
            ValueError: If validation fails.

        """
        self.settings.update(settings)
        self.validate()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value.

        Args:
            key: Setting key.
            default: Default value if key not found.

        Returns:
            Setting value.

        """
        return self.settings.get(key, default)
