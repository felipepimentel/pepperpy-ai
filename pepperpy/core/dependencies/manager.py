"""Dependency management system.

This module provides dependency management functionality:
- Dependency resolution and tracking
- Dependency validation and lifecycle
- Dependency providers and injection
"""

import asyncio
from typing import Any, TypeVar

from pepperpy.core.errors import DependencyError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variable for dependency types
T = TypeVar("T")


class DependencyManager(LifecycleComponent):
    """Manager for dependency lifecycle."""

    def __init__(self) -> None:
        """Initialize manager."""
        super().__init__("dependency_manager")
        self._dependencies: dict[str, Any] = {}
        self._providers: dict[str, Any] = {}
        self._provides: dict[str, set[str]] = {}
        self._depends_on: dict[str, set[str]] = {}
        self._initialized = False
        self._lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """Initialize manager.

        Raises:
            DependencyError: If initialization fails
        """
        await self._validate_dependencies()
        await self._initialize_dependencies()
        self._initialized = True
        logger.info("Dependency manager initialized")

    async def _cleanup(self) -> None:
        """Clean up manager.

        Raises:
            DependencyError: If cleanup fails
        """
        await self._cleanup_dependencies()
        self._initialized = False
        logger.info("Dependency manager cleaned up")

    def register_dependency(
        self,
        name: str,
        dependency: Any,
        dependencies: list[str] | None = None,
    ) -> None:
        """Register a dependency.

        Args:
            name: Dependency name
            dependency: Dependency instance
            dependencies: Optional list of dependency names

        Raises:
            DependencyError: If registration fails
        """
        if name in self._dependencies:
            raise DependencyError(f"Dependency {name} already registered")

        self._dependencies[name] = dependency
        self._depends_on[name] = set(dependencies or [])

        logger.info(
            "Dependency registered",
            extra={
                "name": name,
                "dependencies": list(self._depends_on[name]),
            },
        )

    def register_provider(
        self,
        name: str,
        provider: Any,
        provides: list[str],
    ) -> None:
        """Register a provider.

        Args:
            name: Provider name
            provider: Provider instance
            provides: List of provided dependency names

        Raises:
            DependencyError: If registration fails
        """
        if name in self._providers:
            raise DependencyError(f"Provider {name} already registered")

        self._providers[name] = provider
        self._provides[name] = set(provides)

        logger.info(
            "Provider registered",
            extra={
                "name": name,
                "provides": list(self._provides[name]),
            },
        )

    def unregister_dependency(self, name: str) -> None:
        """Unregister a dependency.

        Args:
            name: Dependency name

        Raises:
            DependencyError: If unregistration fails
        """
        if name not in self._dependencies:
            raise DependencyError(f"Dependency {name} not registered")

        # Check if any other dependencies depend on this one
        for dep_name, deps in self._depends_on.items():
            if name in deps:
                raise DependencyError(
                    f"Cannot unregister {name}: {dep_name} depends on it"
                )

        del self._dependencies[name]
        del self._depends_on[name]

        logger.info("Dependency unregistered", extra={"name": name})

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider.

        Args:
            name: Provider name

        Raises:
            DependencyError: If unregistration fails
        """
        if name not in self._providers:
            raise DependencyError(f"Provider {name} not registered")

        del self._providers[name]
        del self._provides[name]

        logger.info("Provider unregistered", extra={"name": name})

    def get_dependency(self, name: str, type: type[T] | None = None) -> T | Any:
        """Get a dependency.

        Args:
            name: Dependency name
            type: Optional type to validate

        Returns:
            Dependency instance

        Raises:
            DependencyError: If dependency not found or type mismatch
        """
        if name not in self._dependencies:
            raise DependencyError(f"Dependency {name} not found")

        dependency = self._dependencies[name]

        if type is not None and not isinstance(dependency, type):
            raise DependencyError(
                f"Type mismatch for {name}: expected {type.__name__}, got {type(dependency).__name__}"
            )

        return dependency

    def get_provider(self, name: str) -> Any:
        """Get a provider.

        Args:
            name: Provider name

        Returns:
            Provider instance

        Raises:
            DependencyError: If provider not found
        """
        if name not in self._providers:
            raise DependencyError(f"Provider {name} not found")

        return self._providers[name]

    def list_dependencies(self) -> list[str]:
        """List registered dependencies.

        Returns:
            list[str]: List of dependency names
        """
        return list(self._dependencies.keys())

    def list_providers(self) -> list[str]:
        """List registered providers.

        Returns:
            list[str]: List of provider names
        """
        return list(self._providers.keys())

    async def _validate_dependencies(self) -> None:
        """Validate dependency graph.

        Raises:
            DependencyError: If validation fails
        """
        visited: set[str] = set()
        visiting: set[str] = set()

        def check_cycles(node: str) -> None:
            """Check for dependency cycles.

            Args:
                node: Dependency name

            Raises:
                DependencyError: If cycle is detected
            """
            if node in visiting:
                raise DependencyError(f"Dependency cycle detected: {node}")
            if node in visited:
                return

            visiting.add(node)
            for dep in self._depends_on[node]:
                check_cycles(dep)
            visiting.remove(node)
            visited.add(node)

        for name in self._dependencies:
            check_cycles(name)

    async def _initialize_dependencies(self) -> None:
        """Initialize dependencies in dependency order.

        Raises:
            DependencyError: If initialization fails
        """
        initialized: set[str] = set()

        async def initialize_dependency(name: str) -> None:
            """Initialize a dependency and its dependencies.

            Args:
                name: Dependency name

            Raises:
                DependencyError: If initialization fails
            """
            if name in initialized:
                return

            dependency = self._dependencies[name]
            for dep in self._depends_on[name]:
                await initialize_dependency(dep)

            try:
                if hasattr(dependency, "initialize"):
                    await dependency.initialize()
                initialized.add(name)
            except Exception as e:
                raise DependencyError(f"Failed to initialize {name}: {e}")

        for name in self._dependencies:
            await initialize_dependency(name)

    async def _cleanup_dependencies(self) -> None:
        """Clean up dependencies in reverse dependency order.

        Raises:
            DependencyError: If cleanup fails
        """
        cleaned: set[str] = set()

        async def cleanup_dependency(name: str) -> None:
            """Clean up a dependency and its dependents.

            Args:
                name: Dependency name

            Raises:
                DependencyError: If cleanup fails
            """
            if name in cleaned:
                return

            dependency = self._dependencies[name]
            for dep_name, deps in self._depends_on.items():
                if name in deps:
                    await cleanup_dependency(dep_name)

            try:
                if hasattr(dependency, "cleanup"):
                    await dependency.cleanup()
                cleaned.add(name)
            except Exception as e:
                raise DependencyError(f"Failed to clean up {name}: {e}")

        for name in reversed(list(self._dependencies)):
            await cleanup_dependency(name)


__all__ = ["DependencyManager"]
