"""Dependency injection for the PepperPy framework.

This module provides a simple dependency injection system for the PepperPy framework.
It allows for the registration and resolution of dependencies, making it easier to
manage component dependencies and facilitate testing.
"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast, get_type_hints

from pepperpy.core.errors import PepperPyError
from pepperpy.core.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

T = TypeVar("T")
ProviderFunc = Callable[[], T]


class DependencyError(PepperPyError):
    """Error raised when a dependency cannot be resolved."""

    pass


class DependencyContainer:
    """Container for managing dependencies.

    The dependency container is responsible for registering and resolving
    dependencies. It supports registering instances, factory functions,
    and resolving dependencies with automatic injection.
    """

    def __init__(self):
        """Initialize the dependency container."""
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}

    def register_instance(self, interface_type: Type[T], instance: T) -> None:
        """Register an instance for a specific interface type.

        Args:
            interface_type: The interface type to register
            instance: The instance to register
        """
        self._instances[interface_type] = instance
        logger.debug(f"Registered instance of {interface_type.__name__}")

    def register_factory(
        self, interface_type: Type[T], factory: Callable[[], T]
    ) -> None:
        """Register a factory function for a specific interface type.

        Args:
            interface_type: The interface type to register
            factory: The factory function to register
        """
        self._factories[interface_type] = factory
        logger.debug(f"Registered factory for {interface_type.__name__}")

    def resolve(self, interface_type: Type[T]) -> T:
        """Resolve a dependency.

        Args:
            interface_type: The interface type to resolve

        Returns:
            The resolved instance

        Raises:
            DependencyError: If the dependency cannot be resolved
        """
        # Check if we have a registered instance
        if interface_type in self._instances:
            return cast(T, self._instances[interface_type])

        # Check if we have a registered factory
        if interface_type in self._factories:
            factory = self._factories[interface_type]
            instance = factory()
            self._instances[interface_type] = instance
            return cast(T, instance)

        # Try to create an instance
        try:
            instance = self._create_instance(interface_type)
            self._instances[interface_type] = instance
            return cast(T, instance)
        except Exception as e:
            raise DependencyError(
                f"Failed to resolve dependency {interface_type.__name__}: {str(e)}"
            ) from e

    def _create_instance(self, interface_type: Type[T]) -> T:
        """Create an instance of the specified type with dependencies injected.

        Args:
            interface_type: The type to create an instance of

        Returns:
            The created instance

        Raises:
            DependencyError: If the instance cannot be created
        """
        # Get constructor parameter types
        try:
            type_hints = get_type_hints(interface_type.__init__)
        except (AttributeError, TypeError):
            # No constructor or not a class
            raise DependencyError(
                f"Cannot create instance of {interface_type.__name__}: "
                "not a class or no constructor"
            )

        # Remove return type
        if "return" in type_hints:
            del type_hints["return"]

        # Remove self parameter
        if "self" in type_hints:
            del type_hints["self"]

        # Resolve dependencies
        kwargs = {}
        for param_name, param_type in type_hints.items():
            try:
                kwargs[param_name] = self.resolve(param_type)
            except DependencyError as e:
                raise DependencyError(
                    f"Failed to resolve parameter {param_name} of type {param_type.__name__} "
                    f"for {interface_type.__name__}: {str(e)}"
                ) from e

        # Create instance
        try:
            return interface_type(**kwargs)
        except Exception as e:
            raise DependencyError(
                f"Failed to create instance of {interface_type.__name__}: {str(e)}"
            ) from e


class Inject:
    """Decorator for injecting dependencies.

    This decorator can be used to inject dependencies into functions or methods.
    It resolves dependencies from the global dependency container based on
    type hints.

    Example:
        ```python
        @Inject
        def process_data(data_processor: DataProcessor):
            return data_processor.process()
        ```
    """

    def __init__(self, container: Optional[DependencyContainer] = None):
        """Initialize the decorator.

        Args:
            container: Optional dependency container to use
        """
        self.container = container or get_container()

    def __call__(self, func: Callable) -> Callable:
        """Apply the decorator.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        # Get parameter types
        type_hints = get_type_hints(func)

        # Remove return type
        if "return" in type_hints:
            del type_hints["return"]

        # Create wrapper function
        def wrapper(*args, **kwargs):
            # Resolve dependencies for parameters not provided in args or kwargs
            param_names = list(type_hints.keys())

            # Skip self or cls parameter for methods
            if param_names and param_names[0] in ("self", "cls") and args:
                param_names = param_names[1:]
                provided_args = args[1:]
            else:
                provided_args = args

            # Count provided positional arguments
            num_provided_args = len(provided_args)

            # Resolve dependencies for remaining parameters
            for i, param_name in enumerate(param_names):
                if i < num_provided_args or param_name in kwargs:
                    # Parameter already provided
                    continue

                # Resolve dependency
                param_type = type_hints[param_name]
                try:
                    kwargs[param_name] = self.container.resolve(param_type)
                except DependencyError as e:
                    logger.warning(
                        f"Failed to inject parameter {param_name} of type {param_type.__name__} "
                        f"for {func.__name__}: {str(e)}"
                    )

            # Call original function
            return func(*args, **kwargs)

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__annotations__ = func.__annotations__

        return wrapper


# Global dependency container instance
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """Get the global dependency container instance.

    Returns:
        The global dependency container instance
    """
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def set_container(container: DependencyContainer) -> None:
    """Set the global dependency container instance.

    Args:
        container: The dependency container instance to set
    """
    global _container
    _container = container


def register_instance(interface_type: Type[T], instance: T) -> None:
    """Register an instance in the global dependency container.

    Args:
        interface_type: The interface type to register
        instance: The instance to register
    """
    get_container().register_instance(interface_type, instance)


def register_factory(interface_type: Type[T], factory: Callable[[], T]) -> None:
    """Register a factory function in the global dependency container.

    Args:
        interface_type: The interface type to register
        factory: The factory function to register
    """
    get_container().register_factory(interface_type, factory)


def resolve(interface_type: Type[T]) -> T:
    """Resolve a dependency from the global dependency container.

    Args:
        interface_type: The interface type to resolve

    Returns:
        The resolved instance

    Raises:
        DependencyError: If the dependency cannot be resolved
    """
    return get_container().resolve(interface_type)


__all__ = [
    "DependencyContainer",
    "DependencyError",
    "Inject",
    "get_container",
    "set_container",
    "register_instance",
    "register_factory",
    "resolve",
]
