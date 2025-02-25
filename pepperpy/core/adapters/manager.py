"""Adapter manager system.

This module provides adapter management functionality:
- Adapter discovery
- Adapter loading
- Adapter lifecycle
- Adapter monitoring
"""

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any, TypeVar

from pepperpy.core.adapters.base import (
    Adapter,
    AdapterMetadata,
    AdapterState,
    AdapterType,
)
from pepperpy.core.errors import AdapterError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variables for adapter input/output
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class AdapterManager(LifecycleComponent):
    """Manager for adapter lifecycle."""

    def __init__(self, name: str) -> None:
        """Initialize manager.

        Args:
            name: Manager name
        """
        super().__init__(name)
        self._adapters: dict[str, Adapter[Any, Any]] = {}
        self._metadata: dict[str, AdapterMetadata] = {}
        self._paths: set[Path] = set()
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize manager.

        Raises:
            AdapterError: If initialization fails
        """
        try:
            await super().initialize()
            logger.info("Adapter manager initialized", extra={"name": self.name})
        except Exception as e:
            raise AdapterError(f"Failed to initialize adapter manager: {e}")

    async def cleanup(self) -> None:
        """Clean up manager.

        Raises:
            AdapterError: If cleanup fails
        """
        try:
            await super().cleanup()
            async with self._lock:
                for adapter in self._adapters.values():
                    try:
                        await adapter.cleanup()
                    except Exception as e:
                        logger.error(
                            "Failed to clean up adapter",
                            extra={
                                "adapter": adapter.name,
                                "error": str(e),
                            },
                        )
                self._adapters.clear()
                self._metadata.clear()
                self._paths.clear()
            logger.info("Adapter manager cleaned up", extra={"name": self.name})
        except Exception as e:
            raise AdapterError(f"Failed to clean up adapter manager: {e}")

    def add_adapter_path(self, path: Path) -> None:
        """Add adapter search path.

        Args:
            path: Adapter directory path

        Raises:
            AdapterError: If path is invalid
        """
        try:
            if not path.is_dir():
                raise AdapterError(f"Invalid adapter path: {path}")

            self._paths.add(path)
            sys.path.append(str(path))

            logger.info("Added adapter path", extra={"path": str(path)})

        except Exception as e:
            raise AdapterError(f"Failed to add adapter path: {e}")

    async def discover_adapters(self) -> list[AdapterMetadata]:
        """Discover available adapters.

        Returns:
            List of discovered adapter metadata

        Raises:
            AdapterError: If discovery fails
        """
        try:
            discovered = []

            for path in self._paths:
                try:
                    # Find adapter modules
                    for module_path in path.glob("*.py"):
                        if module_path.stem.startswith("_"):
                            continue

                        try:
                            # Import module
                            module_name = module_path.stem
                            spec = importlib.util.spec_from_file_location(
                                module_name, module_path
                            )
                            if not spec or not spec.loader:
                                continue

                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)

                            # Find adapter classes
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if (
                                    isinstance(attr, type)
                                    and issubclass(attr, Adapter)
                                    and attr != Adapter
                                ):
                                    metadata = attr.get_metadata()
                                    discovered.append(metadata)

                        except Exception as e:
                            logger.warning(
                                "Failed to load adapter module",
                                extra={
                                    "module": module_path.name,
                                    "error": str(e),
                                },
                            )

                except Exception as e:
                    logger.error(
                        "Failed to scan adapter path",
                        extra={
                            "path": str(path),
                            "error": str(e),
                        },
                    )

            return discovered

        except Exception as e:
            raise AdapterError(f"Failed to discover adapters: {e}")

    async def load_adapter(
        self,
        name: str,
        adapter_class: type[Adapter[InputT, OutputT]],
        config: dict[str, Any] | None = None,
    ) -> Adapter[InputT, OutputT]:
        """Load adapter.

        Args:
            name: Adapter name
            adapter_class: Adapter class
            config: Optional adapter configuration

        Returns:
            Loaded adapter instance

        Raises:
            AdapterError: If loading fails
        """
        try:
            async with self._lock:
                if name in self._adapters:
                    raise AdapterError(f"Adapter already loaded: {name}")

                # Create adapter instance
                adapter = adapter_class(name, config or {})

                # Initialize adapter
                await adapter.initialize()
                self._adapters[name] = adapter

                # Store metadata
                self._metadata[name] = adapter.get_metadata()

                logger.info(
                    "Loaded adapter",
                    extra={
                        "name": name,
                        "class": adapter_class.__name__,
                    },
                )

                return adapter

        except Exception as e:
            raise AdapterError(f"Failed to load adapter {name}: {e}")

    async def unload_adapter(self, name: str) -> None:
        """Unload adapter.

        Args:
            name: Adapter name

        Raises:
            AdapterError: If unloading fails
        """
        try:
            async with self._lock:
                adapter = self._adapters.get(name)
                if not adapter:
                    raise AdapterError(f"Adapter not found: {name}")

                # Clean up adapter
                await adapter.cleanup()

                # Remove adapter
                del self._adapters[name]
                self._metadata.pop(name, None)

                logger.info("Unloaded adapter", extra={"name": name})

        except Exception as e:
            raise AdapterError(f"Failed to unload adapter {name}: {e}")

    def get_adapter(
        self,
        name: str,
    ) -> Adapter[Any, Any] | None:
        """Get adapter instance.

        Args:
            name: Adapter name

        Returns:
            Adapter instance if found
        """
        return self._adapters.get(name)

    def get_metadata(self, name: str) -> AdapterMetadata | None:
        """Get adapter metadata.

        Args:
            name: Adapter name

        Returns:
            Adapter metadata if found
        """
        return self._metadata.get(name)

    def list_adapters(
        self,
        type: AdapterType | None = None,
        state: AdapterState | None = None,
    ) -> list[Adapter[Any, Any]]:
        """List loaded adapters.

        Args:
            type: Optional adapter type filter
            state: Optional adapter state filter

        Returns:
            List of adapters
        """
        adapters = list(self._adapters.values())

        if type:
            adapters = [a for a in adapters if a.get_metadata().type == type]
        if state:
            adapters = [a for a in adapters if a.state == state]

        return adapters


# Global adapter manager instance
adapter_manager = AdapterManager("global")


# Export public API
__all__ = [
    "AdapterManager",
    "adapter_manager",
]
