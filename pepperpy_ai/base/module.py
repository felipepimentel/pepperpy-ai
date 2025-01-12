"""Base module implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Generic, TypeVar, cast

from ..config.base import BaseConfig
from ..exceptions import ConfigurationError
from ..types import JsonDict

ConfigT = TypeVar("ConfigT", bound=BaseConfig)


class BaseModule(Generic[ConfigT], ABC):
    """Base module implementation."""

    def __init__(self, config: ConfigT) -> None:
        """Initialize module.

        Args:
            config: Module configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.validate_config(config)
        self.config = config
        self._initialized = False
        self._resources: dict[str, Any] = {}

    @property
    def is_initialized(self) -> bool:
        """Check if module is initialized."""
        return self._initialized

    def validate_config(self, config: ConfigT) -> None:
        """Validate module configuration.

        Args:
            config: Configuration to validate

        Raises:
            ConfigurationError: If configuration is invalid
        """
        config_dict = cast(dict[str, Any], config)
        required_fields = {"name", "version", "enabled"}
        missing = required_fields - set(config_dict)
        if missing:
            raise ConfigurationError(
                f"Missing required configuration fields: {missing}",
                field="required_fields"
            )

    async def initialize(self) -> None:
        """Initialize module.

        This method handles the module initialization lifecycle:
        1. Pre-initialization checks
        2. Resource setup
        3. Post-initialization tasks

        Raises:
            ConfigurationError: If module is already initialized
        """
        if self._initialized:
            raise ConfigurationError(
                "Module is already initialized",
                field="initialization_state"
            )

        try:
            await self._pre_setup()
            await self._setup()
            await self._post_setup()
            self._initialized = True
        except Exception as e:
            await self._handle_setup_error(e)

    async def cleanup(self) -> None:
        """Cleanup module resources.

        This method handles the module cleanup lifecycle:
        1. Pre-cleanup tasks
        2. Resource teardown
        3. Post-cleanup tasks
        """
        if not self._initialized:
            return

        try:
            await self._pre_teardown()
            await self._teardown()
            await self._post_teardown()
        finally:
            self._initialized = False
            self._resources.clear()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[None, None]:
        """Context manager for module session.

        This provides a safe way to use the module with automatic
        initialization and cleanup.

        Example:
            async with module.session():
                await module.process_data()
        """
        try:
            await self.initialize()
            yield
        finally:
            await self.cleanup()

    async def _pre_setup(self) -> None:
        """Pre-initialization tasks."""
        pass

    @abstractmethod
    async def _setup(self) -> None:
        """Setup module resources."""
        pass

    async def _post_setup(self) -> None:
        """Post-initialization tasks."""
        pass

    async def _pre_teardown(self) -> None:
        """Pre-cleanup tasks."""
        pass

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown module resources."""
        pass

    async def _post_teardown(self) -> None:
        """Post-cleanup tasks."""
        pass

    async def _handle_setup_error(self, error: Exception) -> None:
        """Handle setup error.

        Args:
            error: The error that occurred during setup
        """
        await self.cleanup()
        if isinstance(error, ConfigurationError):
            raise error
        raise ConfigurationError(
            f"Failed to initialize module: {error}",
            field="initialization"
        )

    def get_resource(self, key: str) -> Any | None:
        """Get module resource.

        Args:
            key: Resource key

        Returns:
            Resource value if exists, None otherwise
        """
        return self._resources.get(key)

    def set_resource(self, key: str, value: Any) -> None:
        """Set module resource.

        Args:
            key: Resource key
            value: Resource value
        """
        self._resources[key] = value

    def get_status(self) -> JsonDict:
        """Get module status.

        Returns:
            Module status information
        """
        config_dict = cast(dict[str, Any], self.config)
        return {
            "name": config_dict["name"],
            "version": config_dict["version"],
            "initialized": self._initialized,
            "resources": list(self._resources.keys())
        }
