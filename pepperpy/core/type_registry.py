"""Type registry functionality for PepperPy.

This module provides a specialized registry for managing type-safe components.
"""

from typing import Dict, List, Optional, Type, TypeVar

from pepperpy.errors import PepperpyError
from pepperpy.registry.base import Registry

# Type variable for registry item types
T = TypeVar("T")


class TypeRegistry(Registry[T]):
    """Registry for type-safe components.

    A type registry ensures that registered components match the expected type.
    It provides methods for registering, retrieving, and listing components.

    Args:
        T: The type of objects that this registry manages
    """

    def __init__(self, registry_name: str, registry_type: str):
        """Initialize the registry.

        Args:
            registry_name: The name of this registry instance
            registry_type: The type of registry (e.g., 'provider', 'schema')
        """
        super().__init__(registry_name, registry_type)
        self._type_registry: Dict[str, Type[T]] = {}
        self._default_id: Optional[str] = None

    def register(self, type_id: str, item_type: Type[T]) -> None:
        """Register a component type.

        Args:
            type_id: The type identifier
            item_type: The component type to register

        Raises:
            PepperpyError: If registration fails
        """
        try:
            self._type_registry[type_id] = item_type
        except Exception as e:
            raise PepperpyError(f"Failed to register type {type_id}: {e}")

    def unregister(self, type_id: str) -> None:
        """Unregister a component type.

        Args:
            type_id: The type identifier to unregister

        Raises:
            PepperpyError: If unregistration fails
        """
        try:
            del self._type_registry[type_id]
        except KeyError:
            raise PepperpyError(f"Type {type_id} not found")
        except Exception as e:
            raise PepperpyError(f"Failed to unregister type {type_id}: {e}")

    def get_type(self, type_id: str) -> Type[T]:
        """Get a registered component type.

        Args:
            type_id: The type identifier

        Returns:
            The registered component type

        Raises:
            PepperpyError: If type is not found
        """
        try:
            return self._type_registry[type_id]
        except KeyError:
            raise PepperpyError(f"Type {type_id} not found")
        except Exception as e:
            raise PepperpyError(f"Failed to get type {type_id}: {e}")

    def list_types(self) -> List[str]:
        """List registered type IDs.

        Returns:
            List of registered type IDs
        """
        return list(self._type_registry.keys())

    def get_default_type(self) -> Optional[str]:
        """Get the default type ID.

        Returns:
            Default type ID if set, None otherwise
        """
        return self._default_id


# Export all classes
__all__ = [
    "TypeRegistry",
]
