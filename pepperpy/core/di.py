"""Enhanced dependency injection for PepperPy.
 
This module provides a comprehensive dependency injection system that supports
constructor injection, property injection, method injection, and lifecycle management.
"""

import inspect
import threading
from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Set, Type, TypeVar, Union, cast, 
    get_type_hints, get_origin, get_args
)

from pepperpy.core.base import PepperpyError

T = TypeVar("T")
K = TypeVar("K")


class DIError(PepperpyError):
    """Base class for dependency injection errors."""
    pass


class ServiceNotFoundError(DIError):
    """Error raised when a service is not found in the container."""
    
    def __init__(self, service_type: Type[Any], name: Optional[str] = None):
        msg = f"Service not found: {service_type.__name__}"
        if name:
            msg += f" with name '{name}'"
        super().__init__(msg)
        self.service_type = service_type
        self.name = name


class CircularDependencyError(DIError):
    """Error raised when a circular dependency is detected."""
    
    def __init__(self, dependency_path: List[str]):
        path_str = " -> ".join(dependency_path)
        super().__init__(f"Circular dependency detected: {path_str}")
        self.dependency_path = dependency_path


class ServiceLifetime(Enum):
    """Service lifetime options."""
    
    # A new instance is created each time the service is requested
    TRANSIENT = 1
    
    # A single instance is created and reused within a scope
    SCOPED = 2
    
    # A single instance is created and reused for the entire application
    SINGLETON = 3


class ServiceDescriptor:
    """Describes a service registration."""
    
    def __init__(
        self,
        service_type: Type[Any],
        implementation_type: Type[Any],
        lifetime: ServiceLifetime,
        name: Optional[str] = None,
        factory: Optional[Callable[..., Any]] = None,
        instance: Optional[Any] = None
    ):
        """Initialize service descriptor.
        
        Args:
            service_type: Type of service to register
            implementation_type: Type that implements the service
            lifetime: Service lifetime
            name: Optional name for the service
            factory: Optional factory function to create the service
            instance: Optional existing instance (for singleton)
        """
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.lifetime = lifetime
        self.name = name
        self.factory = factory
        self.instance = instance


class ServiceProvider:
    """Provides access to services from a dependency injection container."""
    
    def __init__(
        self, 
        descriptors: Dict[str, ServiceDescriptor],
        parent: Optional["ServiceProvider"] = None
    ):
        """Initialize service provider.
        
        Args:
            descriptors: Service descriptors
            parent: Optional parent service provider
        """
        self._descriptors = descriptors
        self._parent = parent
        self._instances: Dict[str, Any] = {}
        
    def get_service(
        self, 
        service_type: Type[T], 
        name: Optional[str] = None
    ) -> T:
        """Get a service instance.
        
        Args:
            service_type: Type of service to get
            name: Optional name for the service
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not found
        """
        key = self._get_key(service_type, name)
        
        # Check if we have the descriptor
        descriptor = self._descriptors.get(key)
        
        if descriptor:
            # Check if we already have an instance for this descriptor
            if key in self._instances:
                return self._instances[key]
                
            # Create a new instance based on lifetime
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                # For singletons, check if we already have an instance
                if descriptor.instance is not None:
                    instance = descriptor.instance
                else:
                    # Create new instance and store it
                    instance = self._create_instance(descriptor)
                    descriptor.instance = instance
                    
                self._instances[key] = instance
                return instance
                
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                # For scoped, create and cache in this provider
                instance = self._create_instance(descriptor)
                self._instances[key] = instance
                return instance
                
            else:  # TRANSIENT
                # For transient, always create a new instance
                return self._create_instance(descriptor)
                
        # Check parent provider if available
        if self._parent:
            return self._parent.get_service(service_type, name)
            
        # Service not found
        raise ServiceNotFoundError(service_type, name)
            
    def get_services(self, service_type: Type[T]) -> List[T]:
        """Get all services of a specific type.
        
        Args:
            service_type: Type of services to get
            
        Returns:
            List of service instances
        """
        services: List[T] = []
        
        # Get services from this provider
        for key, descriptor in self._descriptors.items():
            if descriptor.service_type == service_type:
                services.append(self.get_service(service_type, descriptor.name))
                
        # Get services from parent provider if available
        if self._parent:
            services.extend(self._parent.get_services(service_type))
            
        return services
        
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance of the service.
        
        Args:
            descriptor: Service descriptor
            
        Returns:
            Service instance
        """
        # Use factory if available
        if descriptor.factory:
            return descriptor.factory(self)
            
        # Otherwise create instance using constructor injection
        return self._create_with_injection(descriptor.implementation_type)
        
    def _create_with_injection(
        self, 
        implementation_type: Type[Any],
        dependency_path: Optional[List[str]] = None
    ) -> Any:
        """Create an instance with constructor injection.
        
        Args:
            implementation_type: Type to create
            dependency_path: Current dependency path for circular detection
            
        Returns:
            Created instance
            
        Raises:
            CircularDependencyError: If circular dependency is detected
        """
        # Track dependency path for circular dependency detection
        if dependency_path is None:
            dependency_path = []
            
        type_name = implementation_type.__name__
        if type_name in dependency_path:
            dependency_path.append(type_name)
            raise CircularDependencyError(dependency_path)
            
        new_path = dependency_path + [type_name]
        
        # Get constructor signature
        init_sig = inspect.signature(implementation_type.__init__)
        
        # Get type hints for constructor
        try:
            # Get type hints specifically for __init__
            type_hints = get_type_hints(implementation_type.__init__)
        except (TypeError, NameError):
            # If type hints can't be resolved (common with forward refs)
            # use an empty dict and rely on signature default values
            type_hints = {}
        
        # Build arguments for constructor
        kwargs = {}
        for param_name, param in init_sig.parameters.items():
            # Skip self parameter
            if param_name == "self":
                continue
                
            # If parameter has default value, use it
            if param.default is not inspect.Parameter.empty:
                continue
                
            # Get parameter type
            param_type = type_hints.get(param_name, Any)
            
            # Handle Optional[Type]
            param_is_optional = False
            if get_origin(param_type) is Union:
                args = get_args(param_type)
                if type(None) in args:
                    # It's an Optional[Type]
                    param_is_optional = True
                    # Get the actual type (excluding None)
                    non_none_args = [arg for arg in args if arg is not type(None)]
                    if len(non_none_args) == 1:
                        param_type = non_none_args[0]
                
            try:
                # Try to get service
                kwargs[param_name] = self.get_service(param_type)
            except ServiceNotFoundError:
                if param_is_optional:
                    # For optional dependencies, use None if not found
                    kwargs[param_name] = None
                else:
                    # Re-raise if not optional
                    raise
                
        # Create instance
        instance = implementation_type(**kwargs)
        
        # Apply property injection
        self._apply_property_injection(instance)
        
        return instance
        
    def _apply_property_injection(self, instance: Any) -> None:
        """Apply property injection to an instance.
        
        Args:
            instance: Instance to inject properties into
        """
        # Get class type annotations (for property injection)
        try:
            class_type_hints = get_type_hints(instance.__class__)
        except (TypeError, NameError):
            # If type hints can't be resolved, skip property injection
            return
            
        # Look for properties with Inject annotation
        for prop_name, prop_type in class_type_hints.items():
            # Skip if property already has a value
            if hasattr(instance, prop_name):
                continue
                
            # Skip if property doesn't have Inject annotation
            if not hasattr(instance.__class__, f"__inject_{prop_name}__"):
                continue
                
            # Handle Optional[Type]
            prop_is_optional = False
            if get_origin(prop_type) is Union:
                args = get_args(prop_type)
                if type(None) in args:
                    # It's an Optional[Type]
                    prop_is_optional = True
                    # Get the actual type (excluding None)
                    non_none_args = [arg for arg in args if arg is not type(None)]
                    if len(non_none_args) == 1:
                        prop_type = non_none_args[0]
                
            try:
                # Try to get service
                setattr(instance, prop_name, self.get_service(prop_type))
            except ServiceNotFoundError:
                if prop_is_optional:
                    # For optional dependencies, use None if not found
                    setattr(instance, prop_name, None)
                else:
                    # Re-raise if not optional
                    raise
        
    def _get_key(self, service_type: Type[Any], name: Optional[str] = None) -> str:
        """Get key for service type and name.
        
        Args:
            service_type: Service type
            name: Optional service name
            
        Returns:
            Service key
        """
        if name:
            return f"{service_type.__name__}:{name}"
        return service_type.__name__


class IServiceCollection(ABC):
    """Interface for service collection."""
    
    @abstractmethod
    def add_singleton(
        self, 
        service_type: Type[T], 
        implementation_type: Optional[Type[Any]] = None,
        name: Optional[str] = None
    ) -> "IServiceCollection":
        """Add a singleton service.
        
        Args:
            service_type: Type of service to register
            implementation_type: Type that implements the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        pass
        
    @abstractmethod
    def add_scoped(
        self, 
        service_type: Type[T], 
        implementation_type: Optional[Type[Any]] = None,
        name: Optional[str] = None
    ) -> "IServiceCollection":
        """Add a scoped service.
        
        Args:
            service_type: Type of service to register
            implementation_type: Type that implements the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        pass
        
    @abstractmethod
    def add_transient(
        self, 
        service_type: Type[T], 
        implementation_type: Optional[Type[Any]] = None,
        name: Optional[str] = None
    ) -> "IServiceCollection":
        """Add a transient service.
        
        Args:
            service_type: Type of service to register
            implementation_type: Type that implements the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        pass
        
    @abstractmethod
    def add_singleton_instance(
        self, 
        service_type: Type[T], 
        instance: T,
        name: Optional[str] = None
    ) -> "IServiceCollection":
        """Add an existing instance as a singleton.
        
        Args:
            service_type: Type of service to register
            instance: Instance to register
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        pass
        
    @abstractmethod
    def add_singleton_factory(
        self, 
        service_type: Type[T], 
        factory: Callable[[ServiceProvider], T],
        name: Optional[str] = None
    ) -> "IServiceCollection":
        """Add a singleton factory.
        
        Args:
            service_type: Type of service to register
            factory: Factory function to create the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        pass
        
    @abstractmethod
    def add_scoped_factory(
        self, 
        service_type: Type[T], 
        factory: Callable[[ServiceProvider], T],
        name: Optional[str] = None
    ) -> "IServiceCollection":
        """Add a scoped factory.
        
        Args:
            service_type: Type of service to register
            factory: Factory function to create the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        pass
        
    @abstractmethod
    def add_transient_factory(
        self, 
        service_type: Type[T], 
        factory: Callable[[ServiceProvider], T],
        name: Optional[str] = None
    ) -> "IServiceCollection":
        """Add a transient factory.
        
        Args:
            service_type: Type of service to register
            factory: Factory function to create the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        pass
        
    @abstractmethod
    def build_service_provider(self) -> ServiceProvider:
        """Build a service provider from the service collection.
        
        Returns:
            Service provider
        """
        pass


class ServiceCollection(IServiceCollection):
    """Collection of service descriptors for dependency injection."""
    
    def __init__(self):
        """Initialize service collection."""
        self._descriptors: Dict[str, ServiceDescriptor] = {}
        
    def add_singleton(
        self, 
        service_type: Type[T], 
        implementation_type: Optional[Type[Any]] = None,
        name: Optional[str] = None
    ) -> "ServiceCollection":
        """Add a singleton service.
        
        Args:
            service_type: Type of service to register
            implementation_type: Type that implements the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        impl_type = implementation_type or service_type
        key = self._get_key(service_type, name)
        
        self._descriptors[key] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.SINGLETON,
            name=name
        )
        
        return self
        
    def add_scoped(
        self, 
        service_type: Type[T], 
        implementation_type: Optional[Type[Any]] = None,
        name: Optional[str] = None
    ) -> "ServiceCollection":
        """Add a scoped service.
        
        Args:
            service_type: Type of service to register
            implementation_type: Type that implements the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        impl_type = implementation_type or service_type
        key = self._get_key(service_type, name)
        
        self._descriptors[key] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.SCOPED,
            name=name
        )
        
        return self
        
    def add_transient(
        self, 
        service_type: Type[T], 
        implementation_type: Optional[Type[Any]] = None,
        name: Optional[str] = None
    ) -> "ServiceCollection":
        """Add a transient service.
        
        Args:
            service_type: Type of service to register
            implementation_type: Type that implements the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        impl_type = implementation_type or service_type
        key = self._get_key(service_type, name)
        
        self._descriptors[key] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.TRANSIENT,
            name=name
        )
        
        return self
        
    def add_singleton_instance(
        self, 
        service_type: Type[T], 
        instance: T,
        name: Optional[str] = None
    ) -> "ServiceCollection":
        """Add an existing instance as a singleton.
        
        Args:
            service_type: Type of service to register
            instance: Instance to register
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        key = self._get_key(service_type, name)
        
        self._descriptors[key] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=instance.__class__,
            lifetime=ServiceLifetime.SINGLETON,
            name=name,
            instance=instance
        )
        
        return self
        
    def add_singleton_factory(
        self, 
        service_type: Type[T], 
        factory: Callable[[ServiceProvider], T],
        name: Optional[str] = None
    ) -> "ServiceCollection":
        """Add a singleton factory.
        
        Args:
            service_type: Type of service to register
            factory: Factory function to create the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        key = self._get_key(service_type, name)
        
        self._descriptors[key] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=service_type,
            lifetime=ServiceLifetime.SINGLETON,
            name=name,
            factory=factory
        )
        
        return self
        
    def add_scoped_factory(
        self, 
        service_type: Type[T], 
        factory: Callable[[ServiceProvider], T],
        name: Optional[str] = None
    ) -> "ServiceCollection":
        """Add a scoped factory.
        
        Args:
            service_type: Type of service to register
            factory: Factory function to create the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        key = self._get_key(service_type, name)
        
        self._descriptors[key] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=service_type,
            lifetime=ServiceLifetime.SCOPED,
            name=name,
            factory=factory
        )
        
        return self
        
    def add_transient_factory(
        self, 
        service_type: Type[T], 
        factory: Callable[[ServiceProvider], T],
        name: Optional[str] = None
    ) -> "ServiceCollection":
        """Add a transient factory.
        
        Args:
            service_type: Type of service to register
            factory: Factory function to create the service
            name: Optional name for the service
            
        Returns:
            Self for chaining
        """
        key = self._get_key(service_type, name)
        
        self._descriptors[key] = ServiceDescriptor(
            service_type=service_type,
            implementation_type=service_type,
            lifetime=ServiceLifetime.TRANSIENT,
            name=name,
            factory=factory
        )
        
        return self
        
    def build_service_provider(self) -> ServiceProvider:
        """Build a service provider from the service collection.
        
        Returns:
            Service provider
        """
        return ServiceProvider(dict(self._descriptors))
        
    def _get_key(self, service_type: Type[Any], name: Optional[str] = None) -> str:
        """Get key for service type and name.
        
        Args:
            service_type: Service type
            name: Optional service name
            
        Returns:
            Service key
        """
        if name:
            return f"{service_type.__name__}:{name}"
        return service_type.__name__


class Scope:
    """Scope for dependency injection.
    
    A scope is a container for scoped service instances that are created
    within the scope.
    """
    
    def __init__(self, service_provider: ServiceProvider):
        """Initialize scope.
        
        Args:
            service_provider: Parent service provider
        """
        self._service_provider = ServiceProvider({}, service_provider)
        
    def get_service(self, service_type: Type[T], name: Optional[str] = None) -> T:
        """Get a service instance.
        
        Args:
            service_type: Type of service to get
            name: Optional name for the service
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not found
        """
        return self._service_provider.get_service(service_type, name)
        
    def get_services(self, service_type: Type[T]) -> List[T]:
        """Get all services of a specific type.
        
        Args:
            service_type: Type of services to get
            
        Returns:
            List of service instances
        """
        return self._service_provider.get_services(service_type)


class ContainerScope:
    """Scope context manager for dependency injection."""
    
    def __init__(self, scope: Scope):
        """Initialize container scope.
        
        Args:
            scope: Scope for this context
        """
        self._scope = scope
        
    def __enter__(self) -> Scope:
        """Enter scope context.
        
        Returns:
            Scope
        """
        return self._scope
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit scope context."""
        # Nothing to do here as we don't have disposable services yet
        pass


class Container:
    """Dependency injection container.

    This class provides dependency injection functionality with support for
    singleton, scoped, and transient services.
    """

    # Thread-local storage for active scopes
    _thread_local = threading.local()

    def __init__(self):
        """Initialize the container."""
        self._services = ServiceCollection()
        self._provider = None
        
    @property
    def services(self) -> IServiceCollection:
        """Get the service collection.
        
        Returns:
            Service collection
        """
        return self._services
        
    @property
    def provider(self) -> ServiceProvider:
        """Get the service provider.
        
        Returns:
            Service provider
            
        Raises:
            DIError: If provider is not built yet
        """
        if self._provider is None:
            raise DIError("Service provider not built yet. Call build() first.")
        return self._provider
        
    def build(self) -> "Container":
        """Build the service provider.
        
        Returns:
            Self for chaining
        """
        self._provider = self._services.build_service_provider()
        return self
        
    def create_scope(self) -> ContainerScope:
        """Create a new scope.
        
        Returns:
            Container scope context manager
        """
        if self._provider is None:
            raise DIError("Service provider not built yet. Call build() first.")
            
        scope = Scope(self._provider)
        return ContainerScope(scope)
        
    def get_service(self, service_type: Type[T], name: Optional[str] = None) -> T:
        """Get a service instance.
        
        Args:
            service_type: Type of service to get
            name: Optional name for the service
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not found
        """
        # Check if we have a current scope
        if hasattr(self._thread_local, "current_scope"):
            return self._thread_local.current_scope.get_service(service_type, name)
            
        # Otherwise get from provider
        return self.provider.get_service(service_type, name)
        
    def get_services(self, service_type: Type[T]) -> List[T]:
        """Get all services of a specific type.
        
        Args:
            service_type: Type of services to get
            
        Returns:
            List of service instances
        """
        # Check if we have a current scope
        if hasattr(self._thread_local, "current_scope"):
            return self._thread_local.current_scope.get_services(service_type)
            
        # Otherwise get from provider
        return self.provider.get_services(service_type)
        
    def register(self, cls: Type[T], implementation: Optional[Type[Any]] = None, 
                name: Optional[str] = None, lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> None:
        """Register a class.

        Args:
            cls: Class to register
            implementation: Optional implementation class (defaults to cls)
            name: Optional name for the class
            lifetime: Service lifetime (defaults to SINGLETON)
        """
        if lifetime == ServiceLifetime.SINGLETON:
            self._services.add_singleton(cls, implementation, name)
        elif lifetime == ServiceLifetime.SCOPED:
            self._services.add_scoped(cls, implementation, name)
        else:  # TRANSIENT
            self._services.add_transient(cls, implementation, name)
            
    def resolve(self, cls: Type[T], name: Optional[str] = None) -> T:
        """Resolve a class.

        Args:
            cls: Class to resolve
            name: Optional name for the class

        Returns:
            Instance of the class

        Raises:
            ServiceNotFoundError: If class is not registered
        """
        return self.get_service(cls, name)


# Global container instance
_container = None


def get_container() -> Container:
    """Get the global container instance.
    
    Returns:
        Container instance
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


# Decorator for property injection
def inject(target: Optional[Any] = None):
    """Decorator for property injection.
    
    Args:
        target: Target to inject
        
    Returns:
        Decorated target
    """
    if target is None:
        # Called as @inject
        return inject
        
    # Handle property injection
    if isinstance(target, property):
        # Get the property name from the getter function
        prop_name = target.fget.__name__
        
        # Store injection flag on the class
        setattr(target.fget.__self__, f"__inject_{prop_name}__", True)
        
        return target
        
    # Handle class injection
    if inspect.isclass(target):
        original_init = target.__init__
        
        @wraps(original_init)
        def init_wrapper(self, *args, **kwargs):
            # Call original init
            original_init(self, *args, **kwargs)
            
            # Apply property injection
            container = get_container()
            try:
                # Get type hints for the class
                type_hints = get_type_hints(target)
                
                # Look for properties with Inject annotation
                for prop_name, prop_type in type_hints.items():
                    # Skip if property already has a value
                    if hasattr(self, prop_name) and getattr(self, prop_name) is not None:
                        continue
                        
                    # Skip if property doesn't have Inject annotation
                    if not hasattr(target, f"__inject_{prop_name}__"):
                        continue
                        
                    # Handle Optional[Type]
                    prop_is_optional = False
                    if get_origin(prop_type) is Union:
                        args = get_args(prop_type)
                        if type(None) in args:
                            # It's an Optional[Type]
                            prop_is_optional = True
                            # Get the actual type (excluding None)
                            non_none_args = [arg for arg in args if arg is not type(None)]
                            if len(non_none_args) == 1:
                                prop_type = non_none_args[0]
                        
                    try:
                        # Try to get service
                        setattr(self, prop_name, container.resolve(prop_type))
                    except ServiceNotFoundError:
                        if prop_is_optional:
                            # For optional dependencies, use None if not found
                            setattr(self, prop_name, None)
                        else:
                            # Re-raise if not optional
                            raise
            except Exception:
                # If injection fails, continue without it
                pass
                
        target.__init__ = init_wrapper
        return target
        
    # Handle method injection
    if inspect.isfunction(target) or inspect.ismethod(target):
        @wraps(target)
        def method_wrapper(*args, **kwargs):
            # Apply method injection
            container = get_container()
            try:
                # Get type hints for the method
                type_hints = get_type_hints(target)
                
                # Get signature
                sig = inspect.signature(target)
                
                # Apply injection to missing parameters
                for param_name, param in sig.parameters.items():
                    # Skip if parameter is already provided
                    if param_name in kwargs:
                        continue
                        
                    # Skip if parameter is positional and provided
                    if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                        if len(args) > list(sig.parameters.keys()).index(param_name):
                            continue
                            
                    # Get parameter type
                    param_type = type_hints.get(param_name, Any)
                    
                    # Handle Optional[Type]
                    param_is_optional = False
                    if get_origin(param_type) is Union:
                        args = get_args(param_type)
                        if type(None) in args:
                            # It's an Optional[Type]
                            param_is_optional = True
                            # Get the actual type (excluding None)
                            non_none_args = [arg for arg in args if arg is not type(None)]
                            if len(non_none_args) == 1:
                                param_type = non_none_args[0]
                                
                    try:
                        # Try to get service
                        kwargs[param_name] = container.resolve(param_type)
                    except ServiceNotFoundError:
                        if param_is_optional:
                            # For optional dependencies, use None if not found
                            kwargs[param_name] = None
                        elif param.default is not inspect.Parameter.empty:
                            # Use default value if available
                            kwargs[param_name] = param.default
                        else:
                            # Re-raise if not optional and no default
                            raise
            except Exception:
                # If injection fails, continue without it
                pass
                
            # Call original method
            return target(*args, **kwargs)
            
        return method_wrapper
        
    # Not a valid target
    raise TypeError(f"Cannot apply @inject to {target}")


# Exports
__all__ = [
    "Container",
    "DIError",
    "ServiceLifetime",
    "ServiceNotFoundError",
    "CircularDependencyError",
    "get_container",
    "inject",
]