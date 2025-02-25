"""Import management module for the Pepperpy framework.

This module provides centralized import management including:
- Import tracking
- Lazy imports
- Import profiling
- Circular import prevention
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import logging
import sys
from collections.abc import Sequence
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Any, Protocol, cast

from pepperpy.core.errors import PepperpyError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.monitoring import MonitoringManager
from pepperpy.core.monitoring.types import MonitoringLevel
from pepperpy.utils.imports_hook import ImportOptimizer
from pepperpy.utils.imports_profiler import ImportProfiler
from pepperpy.utils.modules import ModuleManager


class ImportError(PepperpyError):
    """Base class for import-related errors."""


class CircularImportError(ImportError):
    """Error raised when a circular import is detected."""

    def __init__(self, cycle: list[str]) -> None:
        """Initialize error.

        Args:
            cycle: List of module names forming the cycle
        """
        super().__init__(f"Circular import detected: {' -> '.join(cycle)}")
        self.cycle = cycle


class ModuleNotFoundError(ImportError):
    """Error raised when a module cannot be found."""

    def __init__(self, module_name: str) -> None:
        """Initialize error.

        Args:
            module_name: Name of the module that could not be found
        """
        super().__init__(f"Module not found: {module_name}")
        self.module_name = module_name


class MetaPathFinderProtocol(Protocol):
    """Protocol for meta path finders."""

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        """Find module spec."""
        ...


class ImportOptimizer(LifecycleComponent, MetaPathFinderProtocol):
    """Import optimizer component."""

    def __init__(self, name: str = "import_optimizer") -> None:
        """Initialize optimizer.

        Args:
            name: Component name
        """
        super().__init__(name)
        self._monitoring = MonitoringManager(
            name="import_monitoring", export_interval=60.0
        )
        self._import_cache: dict[str, ModuleType] = {}
        self._import_times: dict[str, float] = {}
        self._circular_imports: set[tuple[str, str]] = set()

    async def _initialize(self) -> None:
        """Initialize import optimizer."""
        await self._monitoring.initialize()
        sys.meta_path.insert(0, cast(MetaPathFinderProtocol, self))
        self.logger.debug("Import optimizer initialized")

    async def _cleanup(self) -> None:
        """Clean up import optimizer."""
        sys.meta_path.remove(cast(MetaPathFinderProtocol, self))
        await self._monitoring.cleanup()
        self.logger.debug("Import optimizer cleaned up")

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        """Find module spec.

        Args:
            fullname: Full module name
            path: Optional module search path
            target: Optional target module

        Returns:
            Module spec or None
        """
        # Track import attempt
        asyncio.create_task(
            self._monitoring.record_event(
                level=MonitoringLevel.INFO,
                source="import_optimizer",
                message=f"Import attempt: {fullname}",
                data={"path": path, "target": target and target.__name__},
            )
        )

        # Check for circular imports
        if self._is_circular_import(fullname):
            asyncio.create_task(
                self._monitoring.record_event(
                    level=MonitoringLevel.WARNING,
                    source="import_optimizer",
                    message=f"Circular import detected: {fullname}",
                )
            )
            return None

        # Let other finders handle the actual import
        return None

    def _is_circular_import(self, fullname: str) -> bool:
        """Check for circular imports.

        Args:
            fullname: Full module name

        Returns:
            True if circular import detected
        """
        # Implementation will track import stack and detect cycles
        return False  # Placeholder


class ImportManager(LifecycleComponent):
    """Manager for handling imports safely and efficiently."""

    _instance: ImportManager | None = None

    def __init__(
        self,
        name: str = "import_manager",
        max_cache_size: int | None = None,
        max_cache_entries: int | None = None,
        cache_ttl: float | None = None,
        max_retries: int = 3,
    ) -> None:
        """Initialize manager.

        Args:
            name: Manager name
            max_cache_size: Optional maximum cache size in bytes
            max_cache_entries: Optional maximum number of cache entries
            cache_ttl: Optional cache time-to-live in seconds
            max_retries: Maximum number of import retry attempts
        """
        super().__init__(name)
        self._module_manager = ModuleManager()
        self._optimizer = ImportOptimizer(
            self._module_manager,
            max_cache_size=max_cache_size,
            max_cache_entries=max_cache_entries,
            cache_ttl=cache_ttl,
            max_retries=max_retries,
        )
        self._profiler = ImportProfiler()
        self._monitoring = MonitoringManager(
            name="import_monitoring",
            export_interval=60.0,
        )
        self.logger = logging.getLogger(__name__)

    @classmethod
    def get_instance(cls) -> ImportManager:
        """Get singleton instance.

        Returns:
            Import manager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize manager."""
        # Initialize monitoring
        await self._monitoring.initialize()

        # Register import hook
        sys.meta_path.insert(0, self._optimizer)
        self.logger.debug("Import manager initialized")

    async def cleanup(self) -> None:
        """Clean up manager."""
        # Remove import hook
        try:
            sys.meta_path.remove(self._optimizer)
        except ValueError:
            pass

        # Clean up monitoring
        await self._monitoring.cleanup()
        self.logger.debug("Import manager cleaned up")

    async def lazy_import(
        self,
        module_name: str,
        attribute: str | None = None,
        *,
        package: str | None = None,
    ) -> Any:
        """Lazily import a module or attribute.

        Args:
            module_name: Name of the module to import
            attribute: Optional attribute to import from the module
            package: Optional package name for relative imports

        Returns:
            Imported module or attribute

        Raises:
            ModuleNotFoundError: If the module cannot be found
            ImportError: If there is an error during import
        """
        try:
            # Start profiling
            self._profiler.start_import(module_name)

            # Try to get from cache
            cached = self._optimizer.get(module_name)
            if cached:
                result = cached
                if attribute:
                    result = getattr(cached, attribute)
                self._profiler.finish_import(module_name)
                return result

            # Import module
            module = importlib.import_module(module_name, package)
            if attribute:
                result = getattr(module, attribute)
            else:
                result = module

            # Update cache and finish profiling
            self._optimizer.set(module_name, module)
            profile = self._profiler.finish_import(module_name)

            # Record metrics
            await self._monitoring.record_metric(
                "import_duration_seconds",
                profile.duration,
                labels={"module": module_name},
            )
            await self._monitoring.record_metric(
                "import_memory_bytes",
                profile.memory_delta,
                labels={"module": module_name},
            )

            return result

        except ModuleNotFoundError as e:
            self._profiler.finish_import(module_name, error=str(e))
            raise ModuleNotFoundError(module_name) from e
        except Exception as e:
            self._profiler.finish_import(module_name, error=str(e))
            raise ImportError(f"Error importing {module_name}: {e}") from e

    async def safe_import(
        self,
        module_name: str,
        attribute: str | None = None,
        *,
        default: Any = None,
        package: str | None = None,
    ) -> Any:
        """Safely import a module or attribute.

        Args:
            module_name: Name of the module to import
            attribute: Optional attribute to import from the module
            default: Value to return if import fails
            package: Optional package name for relative imports

        Returns:
            Imported module/attribute or default value
        """
        try:
            return await self.lazy_import(module_name, attribute, package=package)
        except (ModuleNotFoundError, ImportError):
            return default

    async def analyze_imports(self) -> dict[str, Any]:
        """Analyze imports in the system.

        Returns:
            Dictionary containing import analysis results
        """
        # Get profiles
        profiles = self._profiler.analyze_imports()

        # Record metrics
        await self._monitoring.record_metric(
            "total_imports",
            profiles["total_imports"],
        )
        await self._monitoring.record_metric(
            "total_import_errors",
            profiles["error_count"],
        )
        await self._monitoring.record_metric(
            "average_import_duration_seconds",
            profiles["average_duration"],
        )
        await self._monitoring.record_metric(
            "total_import_memory_bytes",
            profiles["total_memory_impact"],
        )

        return profiles

    def get_slow_imports(
        self,
        threshold: float = 0.1,
        include_deps: bool = True,
    ) -> list[dict[str, Any]]:
        """Get slow imports.

        Args:
            threshold: Duration threshold in seconds
            include_deps: Whether to include imports with slow dependencies

        Returns:
            List of slow import profiles
        """
        return [
            {
                "module": p.module,
                "duration": p.duration,
                "memory_delta": p.memory_delta,
                "dependencies": list(p.dependencies),
                "errors": p.errors,
            }
            for p in self._profiler.get_slow_imports(threshold, include_deps)
        ]

    def get_memory_intensive_imports(
        self,
        threshold: int = 1024 * 1024,
        include_deps: bool = True,
    ) -> list[dict[str, Any]]:
        """Get memory intensive imports.

        Args:
            threshold: Memory threshold in bytes
            include_deps: Whether to include imports with memory intensive dependencies

        Returns:
            List of memory intensive import profiles
        """
        return [
            {
                "module": p.module,
                "duration": p.duration,
                "memory_delta": p.memory_delta,
                "dependencies": list(p.dependencies),
                "errors": p.errors,
            }
            for p in self._profiler.get_memory_intensive_imports(
                threshold, include_deps
            )
        ]

    def get_import_chain(self, module: str) -> list[str]:
        """Get import chain for a module.

        Args:
            module: Module name

        Returns:
            List of modules in the import chain
        """
        return self._profiler.get_import_chain(module)


# Global instance
_import_manager = ImportManager.get_instance()


def get_import_manager() -> ImportManager:
    """Get global import manager instance.

    Returns:
        Import manager instance
    """
    return _import_manager


# Export public API
__all__ = [
    "CircularImportError",
    "ImportError",
    "ImportManager",
    "ModuleNotFoundError",
    "get_import_manager",
]
