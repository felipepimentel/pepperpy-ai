"""Adapter registry module.

This module provides a centralized registry for managing adapters and factories.
It implements a singleton pattern and provides thread-safe operations.
"""

import asyncio
import logging
from typing import Dict, Optional

from pepperpy.adapters.base import AdapterFactory, BaseAdapter
from pepperpy.adapters.types import (
    AdapterConfig,
    AdapterMetadata,
    AdapterSpec,
    AdapterState,
)
from pepperpy.core.errors import AdapterError

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """Registry for adapters and factories.

    This class manages adapter registration, creation, and lifecycle.
    It provides thread-safe operations and maintains adapter metadata.
    """

    _instance: Optional["AdapterRegistry"] = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        """Initialize registry."""
        self._adapters: Dict[str, BaseAdapter] = {}
        self._factories: Dict[str, AdapterFactory] = {}
        self._metadata: Dict[str, AdapterMetadata] = {}
        self._specs: Dict[str, AdapterSpec] = {}

    @classmethod
    def get_instance(cls) -> "AdapterRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def register_adapter(
        self,
        adapter: BaseAdapter,
        metadata: Optional[AdapterMetadata] = None,
    ) -> None:
        """Register adapter with optional metadata.

        Args:
            adapter: Adapter instance to register
            metadata: Optional adapter metadata

        Raises:
            AdapterError: If adapter registration fails
        """
        async with self._lock:
            try:
                name = adapter.name
                if name in self._adapters:
                    raise AdapterError(f"Adapter '{name}' already registered")

                self._adapters[name] = adapter
                if metadata:
                    self._metadata[name] = metadata

                logger.info(
                    f"Registered adapter: {name}",
                    extra={
                        "adapter": name,
                        "type": str(adapter.type),
                        "version": adapter.version,
                    },
                )

            except Exception as e:
                logger.error(
                    f"Failed to register adapter: {e}",
                    extra={"adapter": adapter.name},
                    exc_info=True,
                )
                raise AdapterError(f"Failed to register adapter: {e}") from e

    async def register_factory(
        self,
        name: str,
        factory: AdapterFactory,
        spec: AdapterSpec,
    ) -> None:
        """Register adapter factory with specification.

        Args:
            name: Factory name
            factory: Factory instance
            spec: Adapter specification

        Raises:
            AdapterError: If factory registration fails
        """
        async with self._lock:
            try:
                if name in self._factories:
                    raise AdapterError(f"Factory '{name}' already registered")

                self._factories[name] = factory
                self._specs[name] = spec

                logger.info(
                    f"Registered factory: {name}",
                    extra={
                        "factory": name,
                        "type": str(spec.type),
                        "version": spec.version,
                    },
                )

            except Exception as e:
                logger.error(
                    f"Failed to register factory: {e}",
                    extra={"factory": name},
                    exc_info=True,
                )
                raise AdapterError(f"Failed to register factory: {e}") from e

    async def get_adapter(
        self,
        name: str,
        initialize: bool = True,
    ) -> Optional[BaseAdapter]:
        """Get registered adapter by name.

        Args:
            name: Adapter name
            initialize: Whether to initialize adapter if not initialized

        Returns:
            Optional[BaseAdapter]: Adapter instance if found

        Raises:
            AdapterError: If adapter initialization fails
        """
        async with self._lock:
            adapter = self._adapters.get(name)
            if adapter and initialize and adapter.state == AdapterState.CREATED:
                try:
                    await adapter.initialize()
                except Exception as e:
                    logger.error(
                        f"Failed to initialize adapter: {e}",
                        extra={"adapter": name},
                        exc_info=True,
                    )
                    raise AdapterError(f"Failed to initialize adapter: {e}") from e
            return adapter

    async def create_adapter(
        self,
        factory_name: str,
        config: AdapterConfig,
        initialize: bool = True,
    ) -> BaseAdapter:
        """Create and register new adapter instance.

        Args:
            factory_name: Factory name
            config: Adapter configuration
            initialize: Whether to initialize adapter

        Returns:
            BaseAdapter: Created adapter instance

        Raises:
            AdapterError: If adapter creation fails
        """
        async with self._lock:
            try:
                factory = self._factories.get(factory_name)
                if not factory:
                    raise AdapterError(f"Factory '{factory_name}' not found")

                spec = self._specs.get(factory_name)
                if not spec:
                    raise AdapterError(f"Specification for '{factory_name}' not found")

                # Validate configuration against spec
                if spec.validation and spec.validation.config_schema:
                    try:
                        spec.validation.config_schema.validate(config)
                    except Exception as e:
                        raise AdapterError(f"Invalid configuration: {e}")

                # Create adapter instance
                adapter = await factory.create(config)
                if initialize:
                    await adapter.initialize()

                # Register adapter
                await self.register_adapter(adapter)

                return adapter

            except Exception as e:
                logger.error(
                    f"Failed to create adapter: {e}",
                    extra={"factory": factory_name},
                    exc_info=True,
                )
                raise AdapterError(f"Failed to create adapter: {e}") from e

    async def remove_adapter(self, name: str, cleanup: bool = True) -> None:
        """Remove registered adapter.

        Args:
            name: Adapter name
            cleanup: Whether to cleanup adapter resources

        Raises:
            AdapterError: If adapter removal fails
        """
        async with self._lock:
            try:
                adapter = self._adapters.get(name)
                if adapter:
                    if cleanup:
                        await adapter.cleanup()
                    del self._adapters[name]
                    self._metadata.pop(name, None)
                    logger.info(f"Removed adapter: {name}")

            except Exception as e:
                logger.error(
                    f"Failed to remove adapter: {e}",
                    extra={"adapter": name},
                    exc_info=True,
                )
                raise AdapterError(f"Failed to remove adapter: {e}") from e

    async def get_metadata(self, name: str) -> Optional[AdapterMetadata]:
        """Get adapter metadata.

        Args:
            name: Adapter name

        Returns:
            Optional[AdapterMetadata]: Adapter metadata if found
        """
        return self._metadata.get(name)

    async def get_spec(self, name: str) -> Optional[AdapterSpec]:
        """Get adapter specification.

        Args:
            name: Factory name

        Returns:
            Optional[AdapterSpec]: Adapter specification if found
        """
        return self._specs.get(name)

    async def list_adapters(self) -> Dict[str, AdapterMetadata]:
        """List all registered adapters with metadata.

        Returns:
            Dict[str, AdapterMetadata]: Dictionary of adapter names to metadata
        """
        return self._metadata.copy()

    async def list_factories(self) -> Dict[str, AdapterSpec]:
        """List all registered factories with specifications.

        Returns:
            Dict[str, AdapterSpec]: Dictionary of factory names to specifications
        """
        return self._specs.copy() 