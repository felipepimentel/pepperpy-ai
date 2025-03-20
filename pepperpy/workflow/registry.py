"""Pipeline Registry.

This module provides the registry for pipeline components,
including stages, processors, and transformers.
"""

from typing import Dict, Optional, Type, TypeVar

from pepperpy.core import BaseProvider

T = TypeVar("T", bound=BaseProvider)


class Registry:
    """Registry for pipeline components.

    This class manages the registration and retrieval of pipeline
    components such as stages, processors, and transformers.

    Example:
        >>> registry = Registry()
        >>> registry.register("my_stage", MyStage)
        >>> stage = registry.get("my_stage")
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._components: Dict[str, Type[BaseProvider]] = {}

    def register(
        self,
        name: str,
        component_cls: Type[T],
    ) -> None:
        """Register a pipeline component.

        Args:
            name: Component name
            component_cls: Component class

        Raises:
            ValueError: If component is already registered

        Example:
            >>> registry = Registry()
            >>> registry.register("my_stage", MyStage)
        """
        if name in self._components:
            raise ValueError(f"Component already registered: {name}")
        self._components[name] = component_cls

    def get(self, name: str) -> Optional[Type[BaseProvider]]:
        """Get a registered component.

        Args:
            name: Component name

        Returns:
            Component class if found, None otherwise

        Example:
            >>> registry = Registry()
            >>> stage_cls = registry.get("my_stage")
            >>> if stage_cls:
            ...     stage = stage_cls("instance_name")
        """
        return self._components.get(name)

    def list(self) -> Dict[str, Type[BaseProvider]]:
        """List all registered components.

        Returns:
            Dictionary of component names and classes

        Example:
            >>> registry = Registry()
            >>> components = registry.list()
            >>> for name, cls in components.items():
            ...     print(f"{name}: {cls.__name__}")
        """
        return dict(self._components)

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            Registry summary
        """
        return f"Registry({len(self._components)} components)"
