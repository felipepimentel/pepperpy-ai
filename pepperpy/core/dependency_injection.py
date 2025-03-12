"""Dependency injection system for PepperPy.

This module provides a simple dependency injection system for PepperPy,
allowing modules to declare their dependencies and have them injected
at runtime. This helps reduce tight coupling between modules and makes
testing easier by allowing dependencies to be mocked.
"""

import inspect
from typing import Any, Callable, Dict, Type, TypeVar, cast, get_type_hints

T = TypeVar("T")


class DependencyContainer:
    """Container for managing dependencies.

    This class provides a container for managing dependencies and their
    implementations. It allows registering implementations for interfaces
    and resolving dependencies at runtime.

    Example:
        ```python
        # Create a container
        container = DependencyContainer()

        # Register implementations
        container.register(ILogger, ConsoleLogger)
        container.register(IDatabase, SQLiteDatabase)

        # Resolve dependencies
        logger = container.resolve(ILogger)
        database = container.resolve(IDatabase)
        ```
    """

    def __init__(self):
        """Initialize the dependency container."""
        self._registry: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[..., Any]] = {}

    def register(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register an implementation for an interface.

        Args:
            interface: The interface or abstract class to register.
            implementation: The concrete implementation to use.
        """
        self._registry[interface] = implementation

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a singleton instance for an interface.

        Args:
            interface: The interface or abstract class to register.
            instance: The singleton instance to use.
        """
        self._singletons[interface] = instance

    def register_factory(self, interface: Type[T], factory: Callable[..., T]) -> None:
        """Register a factory function for an interface.

        Args:
            interface: The interface or abstract class to register.
            factory: A factory function that creates instances of the implementation.
        """
        self._factories[interface] = factory

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a dependency.

        This method resolves a dependency by looking up the registered
        implementation for the given interface. If a singleton instance
        is registered, it will be returned. If a factory function is
        registered, it will be called to create a new instance. Otherwise,
        a new instance of the registered implementation will be created.

        Args:
            interface: The interface or abstract class to resolve.

        Returns:
            An instance of the registered implementation.

        Raises:
            KeyError: If no implementation is registered for the interface.
            TypeError: If the dependencies of the implementation cannot be resolved.
        """
        # Check if we have a singleton instance
        if interface in self._singletons:
            return cast(T, self._singletons[interface])

        # Check if we have a factory function
        if interface in self._factories:
            factory = self._factories[interface]
            return cast(T, self._inject_dependencies(factory))

        # Check if we have a registered implementation
        if interface in self._registry:
            implementation = self._registry[interface]
            return cast(T, self._create_instance(implementation))

        # If the interface is a concrete class, try to create an instance directly
        if inspect.isclass(interface) and not inspect.isabstract(interface):
            return cast(T, self._create_instance(interface))

        raise KeyError(f"No implementation registered for {interface.__name__}")

    def _create_instance(self, cls: Type) -> Any:
        """Create an instance of a class with dependencies injected.

        Args:
            cls: The class to instantiate.

        Returns:
            An instance of the class with dependencies injected.

        Raises:
            TypeError: If the dependencies of the class cannot be resolved.
        """
        return self._inject_dependencies(cls)

    def _inject_dependencies(self, callable_obj: Callable) -> Any:
        """Inject dependencies into a callable object.

        This method injects dependencies into a callable object (function or class)
        by inspecting its signature and resolving the dependencies for each parameter.

        Args:
            callable_obj: The callable object to inject dependencies into.

        Returns:
            The result of calling the callable object with dependencies injected.

        Raises:
            TypeError: If the dependencies of the callable object cannot be resolved.
        """
        signature = inspect.signature(callable_obj)
        type_hints = get_type_hints(callable_obj)

        args = {}
        for param_name, param in signature.parameters.items():
            # Skip *args and **kwargs
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            # Skip parameters with default values
            if param.default is not param.empty:
                continue

            # Get the type hint for the parameter
            if param_name in type_hints:
                param_type = type_hints[param_name]
                try:
                    args[param_name] = self.resolve(param_type)
                except KeyError:
                    # If we can't resolve the dependency, let it be injected by the caller
                    pass

        return callable_obj(**args)


# Global dependency container
_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """Get the global dependency container.

    Returns:
        The global dependency container.
    """
    return _container


def register(interface: Type[T], implementation: Type[T]) -> None:
    """Register an implementation for an interface in the global container.

    Args:
        interface: The interface or abstract class to register.
        implementation: The concrete implementation to use.
    """
    _container.register(interface, implementation)


def register_instance(interface: Type[T], instance: T) -> None:
    """Register a singleton instance for an interface in the global container.

    Args:
        interface: The interface or abstract class to register.
        instance: The singleton instance to use.
    """
    _container.register_instance(interface, instance)


def register_factory(interface: Type[T], factory: Callable[..., T]) -> None:
    """Register a factory function for an interface in the global container.

    Args:
        interface: The interface or abstract class to register.
        factory: A factory function that creates instances of the implementation.
    """
    _container.register_factory(interface, factory)


def resolve(interface: Type[T]) -> T:
    """Resolve a dependency from the global container.

    Args:
        interface: The interface or abstract class to resolve.

    Returns:
        An instance of the registered implementation.

    Raises:
        KeyError: If no implementation is registered for the interface.
        TypeError: If the dependencies of the implementation cannot be resolved.
    """
    return _container.resolve(interface)


def inject(func: Callable) -> Callable:
    """Decorator for injecting dependencies into a function or method.

    This decorator injects dependencies into a function or method by
    inspecting its signature and resolving the dependencies for each parameter.

    Example:
        ```python
        @inject
        def process_data(logger: ILogger, database: IDatabase):
            logger.info("Processing data...")
            data = database.query("SELECT * FROM data")
            return data
        ```

    Args:
        func: The function or method to inject dependencies into.

    Returns:
        A wrapper function that injects dependencies into the original function.
    """
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)

    def wrapper(*args, **kwargs):
        # Create a new kwargs dict with the original kwargs
        new_kwargs = dict(kwargs)

        # Get the number of positional arguments
        num_pos_args = len(args)

        # Iterate over the parameters
        for i, (param_name, param) in enumerate(signature.parameters.items()):
            # Skip parameters that are already provided as positional args
            if i < num_pos_args:
                continue

            # Skip parameters that are already provided as keyword args
            if param_name in kwargs:
                continue

            # Skip *args and **kwargs
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            # Skip parameters with default values
            if param.default is not param.empty:
                continue

            # Get the type hint for the parameter
            if param_name in type_hints:
                param_type = type_hints[param_name]
                try:
                    new_kwargs[param_name] = _container.resolve(param_type)
                except KeyError:
                    # If we can't resolve the dependency, let it fail naturally
                    pass

        return func(*args, **new_kwargs)

    return wrapper
