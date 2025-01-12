"""Base module implementation."""

from abc import ABC
from collections.abc import Mapping
from typing import Generic, TypedDict, TypeVar

from ..config.base import BaseConfig

T = TypeVar("T", bound=BaseConfig)

class ResourceValue(TypedDict, total=False):
    """Type hints for resource values."""
    value: str | int | float | bool | dict | list | None
    metadata: dict[str, str | int | float | bool | dict | list | None]

class BaseModule(ABC, Generic[T]):
    """Base class for modules.

    This class provides the foundation for implementing different modules.
    Each module can implement its own initialization, cleanup, and resource
    management logic.
    """

    def __init__(self, config: T) -> None:
        """Initialize module.

        Args:
            config: Module configuration.
        """
        self.config = config
        self._initialized = False
        self._resources: dict[str, ResourceValue] = {}

    def _ensure_initialized(self) -> None:
        """Ensure module is initialized.

        Raises:
            RuntimeError: If module is not initialized.
        """
        if not self._initialized:
            raise RuntimeError("Module not initialized")

    def get_resource(self, key: str) -> ResourceValue | None:
        """Get module resource.

        Args:
            key: Resource key.

        Returns:
            ResourceValue | None: Resource value or None if not found.
        """
        return self._resources.get(key)

    def set_resource(self, key: str, value: ResourceValue) -> None:
        """Set module resource.

        Args:
            key: Resource key.
            value: Resource value.
        """
        self._resources[key] = value

    def get_resources(self) -> Mapping[str, ResourceValue]:
        """Get all module resources.

        Returns:
            Mapping[str, ResourceValue]: Dictionary of resources.
        """
        return self._resources
