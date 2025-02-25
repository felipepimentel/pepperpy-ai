"""Adapter factory system.

This module provides adapter factory functionality:
- Adapter creation
- Adapter configuration
- Adapter registration
- Adapter discovery
"""

import asyncio
from typing import Any, Generic, TypeVar

from pepperpy.core.adapters.base import (
    Adapter,
    AdapterMetadata,
    NetworkAdapter,
    ProcessorAdapter,
    ProviderAdapter,
    StorageAdapter,
)
from pepperpy.core.errors import AdapterError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variables for adapter input/output
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class AdapterFactory(LifecycleComponent, Generic[InputT, OutputT]):
    """Factory for creating adapters."""

    def __init__(self, name: str) -> None:
        """Initialize factory.

        Args:
            name: Factory name
        """
        super().__init__(name)
        self._adapter_types: dict[str, type[Adapter[InputT, OutputT]]] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize factory.

        Raises:
            AdapterError: If initialization fails
        """
        try:
            await super().initialize()
            logger.info("Adapter factory initialized", extra={"name": self.name})
        except Exception as e:
            raise AdapterError(f"Failed to initialize adapter factory: {e}")

    async def cleanup(self) -> None:
        """Clean up factory.

        Raises:
            AdapterError: If cleanup fails
        """
        try:
            await super().cleanup()
            async with self._lock:
                self._adapter_types.clear()
            logger.info("Adapter factory cleaned up", extra={"name": self.name})
        except Exception as e:
            raise AdapterError(f"Failed to clean up adapter factory: {e}")

    def register_adapter(
        self,
        type: str,
        adapter_class: type[Adapter[InputT, OutputT]],
    ) -> None:
        """Register adapter type.

        Args:
            type: Adapter type identifier
            adapter_class: Adapter class

        Raises:
            AdapterError: If adapter type is already registered
        """
        if type in self._adapter_types:
            raise AdapterError(f"Adapter type already registered: {type}")

        self._adapter_types[type] = adapter_class
        logger.info(
            "Registered adapter type",
            extra={
                "type": type,
                "class": adapter_class.__name__,
            },
        )

    def unregister_adapter(self, type: str) -> None:
        """Unregister adapter type.

        Args:
            type: Adapter type identifier
        """
        self._adapter_types.pop(type, None)
        logger.info("Unregistered adapter type", extra={"type": type})

    async def create_adapter(
        self,
        type: str,
        name: str,
        config: dict[str, Any] | None = None,
    ) -> Adapter[InputT, OutputT]:
        """Create adapter instance.

        Args:
            type: Adapter type identifier
            name: Adapter name
            config: Optional adapter configuration

        Returns:
            Adapter instance

        Raises:
            AdapterError: If adapter creation fails
        """
        try:
            async with self._lock:
                if type not in self._adapter_types:
                    raise AdapterError(f"Unknown adapter type: {type}")

                adapter_class = self._adapter_types[type]
                adapter = adapter_class(name, config or {})
                await adapter.initialize()

                logger.info(
                    "Created adapter",
                    extra={
                        "type": type,
                        "name": name,
                        "class": adapter_class.__name__,
                    },
                )

                return adapter

        except Exception as e:
            raise AdapterError(f"Failed to create adapter {name}: {e}")

    def get_adapter_class(
        self,
        type: str,
    ) -> type[Adapter[InputT, OutputT]] | None:
        """Get adapter class.

        Args:
            type: Adapter type identifier

        Returns:
            Adapter class if registered
        """
        return self._adapter_types.get(type)

    def list_adapter_types(self) -> dict[str, AdapterMetadata]:
        """List registered adapter types.

        Returns:
            Dictionary mapping type identifiers to metadata
        """
        return {
            type: adapter_class.get_metadata()
            for type, adapter_class in self._adapter_types.items()
        }


class ProviderAdapterFactory(AdapterFactory[InputT, OutputT]):
    """Factory for provider adapters."""

    def __init__(self) -> None:
        """Initialize factory."""
        super().__init__("provider_adapter_factory")

    async def initialize(self) -> None:
        """Initialize factory.

        Registers default provider adapter types.
        """
        await super().initialize()
        self.register_adapter("provider", ProviderAdapter)


class ProcessorAdapterFactory(AdapterFactory[InputT, OutputT]):
    """Factory for processor adapters."""

    def __init__(self) -> None:
        """Initialize factory."""
        super().__init__("processor_adapter_factory")

    async def initialize(self) -> None:
        """Initialize factory.

        Registers default processor adapter types.
        """
        await super().initialize()
        self.register_adapter("processor", ProcessorAdapter)


class StorageAdapterFactory(AdapterFactory[InputT, OutputT]):
    """Factory for storage adapters."""

    def __init__(self) -> None:
        """Initialize factory."""
        super().__init__("storage_adapter_factory")

    async def initialize(self) -> None:
        """Initialize factory.

        Registers default storage adapter types.
        """
        await super().initialize()
        self.register_adapter("storage", StorageAdapter)


class NetworkAdapterFactory(AdapterFactory[InputT, OutputT]):
    """Factory for network adapters."""

    def __init__(self) -> None:
        """Initialize factory."""
        super().__init__("network_adapter_factory")

    async def initialize(self) -> None:
        """Initialize factory.

        Registers default network adapter types.
        """
        await super().initialize()
        self.register_adapter("network", NetworkAdapter)


# Global adapter factories
provider_adapter_factory = ProviderAdapterFactory()
processor_adapter_factory = ProcessorAdapterFactory()
storage_adapter_factory = StorageAdapterFactory()
network_adapter_factory = NetworkAdapterFactory()


# Export public API
__all__ = [
    "AdapterFactory",
    "NetworkAdapterFactory",
    "ProcessorAdapterFactory",
    "ProviderAdapterFactory",
    "StorageAdapterFactory",
    "network_adapter_factory",
    "processor_adapter_factory",
    "provider_adapter_factory",
    "storage_adapter_factory",
]
