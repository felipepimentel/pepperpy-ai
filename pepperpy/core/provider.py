"""
Core provider base classes.

This module provides the base classes and mixins for all PepperPy providers.
"""

from abc import ABC, abstractmethod
from typing import (
    Any,
    Generic,
    Protocol,
    TypeVar,
    cast,
    runtime_checkable,
)

from pepperpy.core.errors import PepperpyError, ValidationError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ProviderError(PepperpyError):
    """Base exception for all provider errors."""

    pass


class InitializationError(ProviderError):
    """Error during provider initialization."""

    pass


class ResourceError(ProviderError):
    """Error related to resource management."""

    pass


@runtime_checkable
class ResourceProvider(Protocol):
    """Protocol for providers that manage resources."""

    async def register_resource(
        self, resource_type: str, resource_id: str, resource: Any
    ) -> None:
        """Register a resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            resource: Resource object
        """
        ...

    async def get_resource(self, resource_type: str, resource_id: str) -> Any:
        """Get a registered resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier

        Returns:
            Resource object

        Raises:
            ResourceError: If resource not found
        """
        ...

    async def cleanup_resources(self) -> None:
        """Clean up all resources owned by this provider."""
        ...


class BaseProvider(ABC):
    """Base class for all PepperPy providers.

    This class implements common provider functionality including:
    - Configuration management
    - Initialization and cleanup lifecycle
    - Error handling patterns
    - Common utility methods

    All domain-specific providers should inherit from this class.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the provider with configuration.

        Args:
            config: Provider configuration dictionary
        """
        self.config = config or {}
        self.initialized = False
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self.logger.debug(f"Created provider with config: {self.config}")

    async def initialize(self) -> None:
        """Initialize provider resources.

        This method implements the common initialization pattern:
        1. Check if already initialized
        2. Validate configuration
        3. Call implementation-specific initialization
        4. Mark as initialized

        Raises:
            InitializationError: If initialization fails
        """
        if self.initialized:
            return

        try:
            # Validate configuration before initializing
            self._validate_config()

            # Call implementation-specific initialization
            await self._initialize_resources()

            self.initialized = True
            self.logger.info(f"Initialized provider: {self.__class__.__name__}")
        except Exception as e:
            self.logger.error(f"Error initializing provider: {e}")
            raise InitializationError(
                f"Failed to initialize {self.__class__.__name__}: {e}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method implements the common cleanup pattern:
        1. Check if initialized
        2. Call implementation-specific cleanup
        3. Clean up resources if resource provider
        4. Mark as not initialized

        Resources are always cleaned up, even if errors occur.
        """
        if not self.initialized:
            return

        self.logger.info(f"Cleaning up provider: {self.__class__.__name__}")

        try:
            # Call implementation-specific cleanup
            await self._cleanup_resources()

            # Clean up resources if this is a resource provider
            if isinstance(self, ResourceProvider):
                await self.cleanup_resources()

        except Exception as e:
            self.logger.error(f"Error during provider cleanup: {e}")
        finally:
            self.initialized = False

    def _validate_config(self) -> None:
        """Validate provider configuration.

        Validates that all required configuration options are present and valid.
        Default implementation does basic validation of required fields.

        Raises:
            ValidationError: If configuration is invalid
        """
        # Check required fields
        for field in self.get_required_config_fields():
            if field not in self.config:
                raise ValidationError(f"Missing required configuration field: {field}")

    def get_required_config_fields(self) -> list[str]:
        """Get list of required configuration fields.

        Override this method to specify required configuration fields.

        Returns:
            List of required field names
        """
        return []

    def get_optional_config_fields(self) -> dict[str, Any]:
        """Get dictionary of optional configuration fields and default values.

        Override this method to specify optional configuration fields and defaults.

        Returns:
            Dictionary of field names and default values
        """
        return {}

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with fallback.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if key in self.config:
            return self.config[key]

        # Check in optional fields for default
        optional_fields = self.get_optional_config_fields()
        if key in optional_fields:
            return optional_fields[key]

        return default

    @abstractmethod
    async def _initialize_resources(self) -> None:
        """Initialize provider-specific resources.

        This method should be implemented by concrete provider classes to
        perform their specific initialization logic.

        Raises:
            InitializationError: If initialization fails
        """
        pass

    @abstractmethod
    async def _cleanup_resources(self) -> None:
        """Clean up provider-specific resources.

        This method should be implemented by concrete provider classes to
        perform their specific cleanup logic.
        """
        pass

    async def __aenter__(self) -> "BaseProvider":
        """Context manager entry.

        Returns:
            Self for use in context manager
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        await self.cleanup()


class GenericProvider(Generic[T], BaseProvider):
    """Generic provider with type parameter.

    This class extends BaseProvider with a type parameter for providers
    that work with specific types.

    Type Parameters:
        T: The type this provider works with
    """

    async def can_handle(self, obj: Any) -> bool:
        """Check if this provider can handle the given object.

        Args:
            obj: Object to check

        Returns:
            True if can handle, False otherwise
        """
        return isinstance(obj, self._get_handled_type())

    def _get_handled_type(self) -> type:
        """Get the type this provider handles.

        Returns:
            Type handled by this provider
        """
        return cast(type, T)
