"""Dependency injection for PepperPy.
 
This module provides dependency injection functionality.
"""


import inspect
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T")


class Container:
    """Dependency injection container.

    This class provides dependency injection functionality.
    """

    def __init__(self):
        """Initialize the container."""
        self._registry: Dict[str, Type[Any]] = {}

    def register(self, cls: Type[T], name: Optional[str] = None) -> None:
        """Register a class.

        Args:
            cls: Class to register
            name: Optional name for the class
        """
        key = self._get_key(cls, name)
        self._registry[key] = cls

    def resolve(self, cls: Type[T], name: Optional[str] = None) -> T:
        """Resolve a class.

        Args:
            cls: Class to resolve
            name: Optional name for the class

        Returns:
            Instance of the class

        Raises:
            KeyError: If class is not registered
        """
        key = self._get_key(cls, name)
        if key not in self._registry:
            registered_cls = cls
        else:
            registered_cls = self._registry[key]

        return self._create_instance(registered_cls)

    def _create_instance(self, cls: Type[T]) -> T:
        """Create an instance of the class.

        This method handles dependency injection by inspecting the class
        constructor and resolving its dependencies.

        Args:
            cls: Class to create instance of

        Returns:
            Instance of the class
        """
        # Get constructor signature
        sig = inspect.signature(cls.__init__)

        # Collect parameters
        params = {}
        for param_name, param in sig.parameters.items():
            # Skip self parameter
            if param_name == "self":
                continue

            # Skip parameters with default values
            if param.default is not inspect.Parameter.empty:
                continue

            # Resolve parameter
            if param.annotation is not inspect.Parameter.empty:
                params[param_name] = self.resolve(param.annotation)

        # Create instance
        return cls(**params)

    def _get_key(self, cls: Type[Any], name: Optional[str] = None) -> str:
        """Get key for registry.

        Args:
            cls: Class to get key for
            name: Optional name for the class

        Returns:
            Key for registry
        """
        if name:
            return f"{cls.__name__}:{name}"
        return cls.__name__
