"""Auto-registration utilities for the registry system.

This module provides utilities for automatically registering components
with the registry system based on decorators and module scanning.
"""

import logging
from functools import wraps
from typing import Any, Dict, Optional, Type, TypeVar

from pepperpy.core.registry.base import (
    Registry,
    RegistryComponent,
    get_registry,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=RegistryComponent)

# Dictionary to store registration info for classes
_registry_info_store: Dict[Type, Dict[str, Any]] = {}


def register_component(registry_name: str, component_name: Optional[str] = None):
    """Decorator for auto-registering components with a registry.

    Args:
        registry_name: Name of the registry to register with
        component_name: Optional name to register the component under

    Returns:
        Decorator function
    """

    def decorator(cls: Type[T]) -> Type[T]:
        """Decorator function.

        Args:
            cls: Component class to register

        Returns:
            Original component class
        """
        # Store registration info in the global store
        _registry_info_store[cls] = {
            "registry_name": registry_name,
            "component_name": component_name or cls.__name__,
        }

        @wraps(cls.__init__)
        def wrapped_init(self, *args, **kwargs):
            """Wrapped initialization function.

            This function calls the original __init__ and then
            attempts to register the component with the registry.
            """
            # Call original init
            original_init(self, *args, **kwargs)

            # Try to register the component
            try:
                registry_manager = get_registry()
                registry = registry_manager.get_registry(registry_name)
                name = component_name or self.name
                registry.register(self)
                logger.debug(f"Auto-registered component {name} with {registry_name}")
            except Exception as e:
                logger.warning(f"Failed to auto-register component: {e}")

        # Store original init
        original_init = cls.__init__
        cls.__init__ = wrapped_init  # type: ignore

        return cls

    return decorator


def initialize_registry_system() -> Dict[str, Registry[Any]]:
    """Initialize the registry system.

    This function initializes the registry system by creating
    the registry manager and scanning for registries.

    Returns:
        Dictionary of registered registries
    """
    # Get registry manager
    registry_manager = get_registry()

    # Return registered registries
    return registry_manager.list_registries()
