"""Base factory classes for Pepperpy."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Type, TypeVar

from ...common.types import PepperpyObject, DictInitializable
from ...common.errors import PepperpyError
from .component import Component
from .config import BaseConfig

T = TypeVar("T", bound=Component)
C = TypeVar("C", bound=BaseConfig)

class Factory(PepperpyObject, DictInitializable, Generic[T, C], ABC):
    """Base class for all Pepperpy factories."""
    
    def __init__(self, config: C) -> None:
        """Initialize factory.
        
        Args:
            config: Factory configuration
        """
        self._config = config
        self._instances: Dict[str, T] = {}
        
    @property
    def config(self) -> C:
        """Return factory configuration."""
        return self._config
        
    def get_instance(self, name: str) -> Optional[T]:
        """Get existing instance by name.
        
        Args:
            name: Instance name
            
        Returns:
            Instance if exists, None otherwise
        """
        return self._instances.get(name)
        
    def create(self, name: str, **kwargs: Any) -> T:
        """Create new instance.
        
        Args:
            name: Instance name
            **kwargs: Additional arguments for instance creation
            
        Returns:
            Created instance
            
        Raises:
            PepperpyError: If instance creation fails
        """
        if name in self._instances:
            raise PepperpyError(f"Instance {name} already exists")
            
        try:
            instance = self._create(name, **kwargs)
            self._instances[name] = instance
            return instance
            
        except Exception as e:
            raise PepperpyError(f"Failed to create instance {name}: {str(e)}") from e
            
    def get_or_create(self, name: str, **kwargs: Any) -> T:
        """Get existing instance or create new one.
        
        Args:
            name: Instance name
            **kwargs: Additional arguments for instance creation
            
        Returns:
            Instance
        """
        instance = self.get_instance(name)
        if instance is None:
            instance = self.create(name, **kwargs)
        return instance
        
    @abstractmethod
    def _create(self, name: str, **kwargs: Any) -> T:
        """Create instance implementation to be provided by subclasses."""
        ...
        
    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(config={self.config})"
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Factory":
        """Create factory from dictionary.
        
        Args:
            data: Dictionary with factory data
            
        Returns:
            Factory instance
        """
        config_cls = cls.get_config_class()
        config = config_cls.from_dict(data["config"])
        return cls(config=config)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert factory to dictionary.
        
        Returns:
            Dictionary with factory data
        """
        return {
            "config": self.config.to_dict(),
        }
        
    @classmethod
    @abstractmethod
    def get_config_class(cls) -> Type[C]:
        """Return configuration class for this factory."""
        ... 