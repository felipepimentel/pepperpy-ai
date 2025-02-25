"""Dependency management system.

This module provides dependency management functionality:
- Dependency resolution
- Dependency tracking
- Dependency validation
- Dependency lifecycle
"""

from typing import Any, TypeVar

from pepperpy.core.errors import DependencyError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variable for dependency values
T = TypeVar("T")


class DependencyManager(LifecycleComponent):
    """Manages dependencies and their lifecycle."""

    def __init__(self) -> None:
        """Initialize dependency manager."""
        super().__init__("dependency_manager")
        self._dependencies: dict[str, Any] = {}
        self._providers: dict[str, Any] = {}
        self._graph: dict[str, set[str]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize dependency manager.

        Raises:
            DependencyError: If initialization fails
        """
        try:
            await super().initialize()
            await self._validate_dependencies()
            await self._initialize_dependencies()
            self._initialized = True
            logger.info("Dependency manager initialized")
        except Exception as e:
            raise DependencyError(f"Failed to initialize dependency manager: {e}")

    async def cleanup(self) -> None:
        """Clean up dependency manager.

        Raises:
            DependencyError: If cleanup fails
        """
        try:
            await super().cleanup()
            await self._cleanup_dependencies()
            self._initialized = False
            logger.info("Dependency manager cleaned up")
        except Exception as e:
            raise DependencyError(f"Failed to clean up dependency manager: {e}")

    def register_dependency(
        self,
        name: str,
        dependency: Any,
        dependencies: list[str] | None = None,
    ) -> None:
        """Register dependency.

        Args:
            name: Dependency name
            dependency: Dependency instance or class
            dependencies: List of dependency names this dependency depends on

        Raises:
            DependencyError: If registration fails
        """
        if name in self._dependencies:
            raise DependencyError(f"Dependency {name} already registered")

        self._dependencies[name] = dependency
        if dependencies:
            self._graph[name] = set(dependencies)
            for dep in dependencies:
                if dep not in self._dependencies:
                    raise DependencyError(f"Unknown dependency {dep}")
        else:
            self._graph[name] = set()

        logger.info(
            "Dependency registered",
            extra={
                "name": name,
                "dependencies": dependencies,
            },
        )

    def register_provider(
        self,
        name: str,
        provider: Any,
        provides: list[str],
    ) -> None:
        """Register dependency provider.

        Args:
            name: Provider name
            provider: Provider instance or class
            provides: List of dependency names this provider provides

        Raises:
            DependencyError: If registration fails
        """
        if name in self._providers:
            raise DependencyError(f"Provider {name} already registered")

        self._providers[name] = provider
        for dep in provides:
            if dep in self._dependencies:
                raise DependencyError(f"Dependency {dep} already registered")

        logger.info(
            "Provider registered",
            extra={
                "name": name,
                "provides": provides,
            },
        )

    def unregister_dependency(self, name: str) -> None:
        """Unregister dependency.

        Args:
            name: Dependency name

        Raises:
            DependencyError: If unregistration fails
        """
        if name not in self._dependencies:
            raise DependencyError(f"Unknown dependency {name}")

        # Check if any other dependencies depend on this one
        for dep, deps in self._graph.items():
            if name in deps:
                raise DependencyError(f"Cannot unregister {name}, {dep} depends on it")

        del self._dependencies[name]
        del self._graph[name]

        logger.info(
            "Dependency unregistered",
            extra={"name": name},
        )

    def unregister_provider(self, name: str) -> None:
        """Unregister provider.

        Args:
            name: Provider name

        Raises:
            DependencyError: If unregistration fails
        """
        if name not in self._providers:
            raise DependencyError(f"Unknown provider {name}")

        del self._providers[name]

        logger.info(
            "Provider unregistered",
            extra={"name": name},
        )

    def get_dependency(self, name: str, type: type[T] | None = None) -> T | Any:
        """Get dependency instance.

        Args:
            name: Dependency name
            type: Expected dependency type

        Returns:
            Dependency instance

        Raises:
            DependencyError: If dependency not found or type mismatch
        """
        if not self._initialized:
            raise DependencyError("Dependency manager not initialized")

        if name not in self._dependencies:
            raise DependencyError(f"Unknown dependency {name}")

        dependency = self._dependencies[name]
        if type and not isinstance(dependency, type):
            raise DependencyError(
                f"Type mismatch for {name}: expected {type}, got {type(dependency)}"
            )

        return dependency

    def get_provider(self, name: str) -> Any:
        """Get provider instance.

        Args:
            name: Provider name

        Returns:
            Provider instance

        Raises:
            DependencyError: If provider not found
        """
        if name not in self._providers:
            raise DependencyError(f"Unknown provider {name}")

        return self._providers[name]

    def list_dependencies(self) -> list[str]:
        """List registered dependencies.

        Returns:
            List of dependency names
        """
        return list(self._dependencies.keys())

    def list_providers(self) -> list[str]:
        """List registered providers.

        Returns:
            List of provider names
        """
        return list(self._providers.keys())

    async def _validate_dependencies(self) -> None:
        """Validate dependency graph.

        Raises:
            DependencyError: If validation fails
        """
        # Check for cycles
        visited: set[str] = set()
        path: set[str] = set()

        def check_cycles(node: str) -> None:
            if node in path:
                cycle = " -> ".join(list(path) + [node])
                raise DependencyError(f"Dependency cycle detected: {cycle}")
            if node in visited:
                return

            visited.add(node)
            path.add(node)
            for dep in self._graph[node]:
                check_cycles(dep)
            path.remove(node)

        for node in self._graph:
            check_cycles(node)

        logger.info("Dependencies validated")

    async def _initialize_dependencies(self) -> None:
        """Initialize dependencies.

        Raises:
            DependencyError: If initialization fails
        """
        # Initialize in dependency order
        initialized: set[str] = set()

        async def initialize_dependency(name: str) -> None:
            if name in initialized:
                return

            # Initialize dependencies first
            for dep in self._graph[name]:
                await initialize_dependency(dep)

            # Initialize dependency
            dependency = self._dependencies[name]
            if isinstance(dependency, LifecycleComponent):
                try:
                    await dependency.initialize()
                except Exception as e:
                    raise DependencyError(
                        f"Failed to initialize dependency {name}: {e}"
                    )

            initialized.add(name)

        for name in self._dependencies:
            await initialize_dependency(name)

        logger.info("Dependencies initialized")

    async def _cleanup_dependencies(self) -> None:
        """Clean up dependencies.

        Raises:
            DependencyError: If cleanup fails
        """
        # Clean up in reverse dependency order
        cleaned: set[str] = set()

        async def cleanup_dependency(name: str) -> None:
            if name in cleaned:
                return

            # Clean up dependencies that depend on this one first
            dependents = {dep for dep, deps in self._graph.items() if name in deps}
            for dep in dependents:
                await cleanup_dependency(dep)

            # Clean up dependency
            dependency = self._dependencies[name]
            if isinstance(dependency, LifecycleComponent):
                try:
                    await dependency.cleanup()
                except Exception as e:
                    raise DependencyError(f"Failed to clean up dependency {name}: {e}")

            cleaned.add(name)

        for name in reversed(list(self._dependencies)):
            await cleanup_dependency(name)

        logger.info("Dependencies cleaned up")
