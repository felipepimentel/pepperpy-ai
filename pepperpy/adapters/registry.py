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
from pepperpy.core.registry import (
    ComponentMetadata,
    Registry,
    get_registry,
)

logger = logging.getLogger(__name__)


class AdapterRegistry(Registry[BaseAdapter]):
    """Registry for adapters and factories.

    This class manages adapter registration, creation, and lifecycle.
    It provides thread-safe operations and maintains adapter metadata.
    """

    _instance: Optional["AdapterRegistry"] = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        """Initialize registry."""
        super().__init__(BaseAdapter)
        self._factories: Dict[str, AdapterFactory] = {}
        self._adapter_metadata: Dict[str, AdapterMetadata] = {}
        self._specs: Dict[str, AdapterSpec] = {}

    @classmethod
    def get_instance(cls) -> "AdapterRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            # Register with the global registry manager
            try:
                registry_manager = get_registry()
                registry_manager.register_registry("adapters", cls._instance)
            except Exception as e:
                logger.warning(f"Failed to register with global registry: {e}")
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

                # Create component metadata
                component_metadata = ComponentMetadata(
                    name=name,
                    description=getattr(adapter, "description", ""),
                    version=adapter.version,
                    properties={
                        "type": str(adapter.type),
                        "state": str(adapter.state),
                    },
                )

                # Register with unified registry
                self.register(adapter, component_metadata)

                # Store adapter-specific metadata
                if metadata:
                    self._adapter_metadata[name] = metadata

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
            try:
                adapter = self.get(name)
                if initialize and adapter.state == AdapterState.CREATED:
                    try:
                        await adapter.initialize()

                        # Update metadata
                        metadata = self.get_metadata(name)
                        metadata.properties["state"] = str(adapter.state)
                    except Exception as e:
                        logger.error(
                            f"Failed to initialize adapter: {e}",
                            extra={"adapter": name},
                            exc_info=True,
                        )
                        raise AdapterError(f"Failed to initialize adapter: {e}") from e
                return adapter
            except Exception as e:
                if "not found" in str(e).lower():
                    return None
                raise AdapterError(f"Error getting adapter: {e}") from e

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
                adapter = None
                try:
                    adapter = self.get(name)
                except Exception:
                    return

                if adapter:
                    if cleanup:
                        await adapter.cleanup()
                    self.unregister(name)
                    self._adapter_metadata.pop(name, None)
                    logger.info(f"Removed adapter: {name}")

            except Exception as e:
                logger.error(
                    f"Failed to remove adapter: {e}",
                    extra={"adapter": name},
                    exc_info=True,
                )
                raise AdapterError(f"Failed to remove adapter: {e}") from e

    async def get_adapter_metadata(self, name: str) -> Optional[AdapterMetadata]:
        """Get adapter-specific metadata.

        Args:
            name: Adapter name

        Returns:
            Optional[AdapterMetadata]: Adapter metadata if found
        """
        async with self._lock:
            return self._adapter_metadata.get(name)

    async def get_spec(self, name: str) -> Optional[AdapterSpec]:
        """Get factory specification.

        Args:
            name: Factory name

        Returns:
            Optional[AdapterSpec]: Factory specification if found
        """
        async with self._lock:
            return self._specs.get(name)

    async def list_adapters(self) -> Dict[str, ComponentMetadata]:
        """List registered adapters with metadata.

        Returns:
            Dict[str, ComponentMetadata]: Dictionary of adapter metadata
        """
        async with self._lock:
            return self.list_metadata()

    async def list_factories(self) -> Dict[str, AdapterSpec]:
        """List registered factories with specifications.

        Returns:
            Dict[str, AdapterSpec]: Dictionary of factory specifications
        """
        async with self._lock:
            return self._specs.copy()
