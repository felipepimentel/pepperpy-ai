"""Base registry classes for Pepperpy."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Set, Type, TypeVar

from ...common.types import PepperpyObject, DictInitializable
from ...common.errors import PepperpyError
from .component import Component
from .factory import Factory

T = TypeVar("T", bound=Component)
F = TypeVar("F", bound=Factory)

class Registry(PepperpyObject, DictInitializable, Generic[T, F], ABC):
    """Base class for all Pepperpy registries."""
    
    def __init__(self) -> None:
        """Initialize registry."""
        self._factories: Dict[str, F] = {}
        self._instances: Dict[str, T] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        
    def register_factory(self, name: str, factory: F) -> None:
        """Register factory.
        
        Args:
            name: Factory name
            factory: Factory instance
            
        Raises:
            PepperpyError: If factory already exists
        """
        if name in self._factories:
            raise PepperpyError(f"Factory {name} already registered")
            
        self._factories[name] = factory
        
    def unregister_factory(self, name: str) -> None:
        """Unregister factory.
        
        Args:
            name: Factory name
        """
        self._factories.pop(name, None)
        
    def get_factory(self, name: str) -> Optional[F]:
        """Get factory by name.
        
        Args:
            name: Factory name
            
        Returns:
            Factory if exists, None otherwise
        """
        return self._factories.get(name)
        
    def register_instance(self, name: str, instance: T) -> None:
        """Register instance.
        
        Args:
            name: Instance name
            instance: Instance to register
            
        Raises:
            PepperpyError: If instance already exists
        """
        if name in self._instances:
            raise PepperpyError(f"Instance {name} already registered")
            
        self._instances[name] = instance
        self._dependencies[name] = set()
        
    def unregister_instance(self, name: str) -> None:
        """Unregister instance.
        
        Args:
            name: Instance name
        """
        self._instances.pop(name, None)
        self._dependencies.pop(name, None)
        
        # Remove from other instances' dependencies
        for deps in self._dependencies.values():
            deps.discard(name)
        
    def get_instance(self, name: str) -> Optional[T]:
        """Get instance by name.
        
        Args:
            name: Instance name
            
        Returns:
            Instance if exists, None otherwise
        """
        return self._instances.get(name)
        
    def add_dependency(self, instance_name: str, dependency_name: str) -> None:
        """Add dependency between instances.
        
        Args:
            instance_name: Instance name
            dependency_name: Dependency name
            
        Raises:
            PepperpyError: If instance or dependency does not exist
        """
        if instance_name not in self._instances:
            raise PepperpyError(f"Instance {instance_name} not found")
            
        if dependency_name not in self._instances:
            raise PepperpyError(f"Dependency {dependency_name} not found")
            
        self._dependencies[instance_name].add(dependency_name)
        
    def remove_dependency(self, instance_name: str, dependency_name: str) -> None:
        """Remove dependency between instances.
        
        Args:
            instance_name: Instance name
            dependency_name: Dependency name
        """
        if instance_name in self._dependencies:
            self._dependencies[instance_name].discard(dependency_name)
        
    def get_dependencies(self, name: str) -> Set[str]:
        """Get instance dependencies.
        
        Args:
            name: Instance name
            
        Returns:
            Set of dependency names
        """
        return self._dependencies.get(name, set())
        
    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(factories={len(self._factories)}, instances={len(self._instances)})"
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Registry":
        """Create registry from dictionary.
        
        Args:
            data: Dictionary with registry data
            
        Returns:
            Registry instance
        """
        registry = cls()
        
        # Register factories
        for name, factory_data in data.get("factories", {}).items():
            factory_cls = cls.get_factory_class()
            factory = factory_cls.from_dict(factory_data)
            registry.register_factory(name, factory)
            
        # Register instances
        for name, instance_data in data.get("instances", {}).items():
            instance = registry._create_instance(instance_data)
            registry.register_instance(name, instance)
            
        # Add dependencies
        for name, deps in data.get("dependencies", {}).items():
            for dep in deps:
                registry.add_dependency(name, dep)
                
        return registry
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert registry to dictionary.
        
        Returns:
            Dictionary with registry data
        """
        return {
            "factories": {
                name: factory.to_dict()
                for name, factory in self._factories.items()
            },
            "instances": {
                name: self._serialize_instance(instance)
                for name, instance in self._instances.items()
            },
            "dependencies": {
                name: list(deps)
                for name, deps in self._dependencies.items()
            },
        }
        
    @classmethod
    @abstractmethod
    def get_factory_class(cls) -> Type[F]:
        """Return factory class for this registry."""
        ...
        
    @abstractmethod
    def _create_instance(self, data: Dict[str, Any]) -> T:
        """Create instance from dictionary."""
        ...
        
    @abstractmethod
    def _serialize_instance(self, instance: T) -> Dict[str, Any]:
        """Convert instance to dictionary."""
        ... 