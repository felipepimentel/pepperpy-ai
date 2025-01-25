"""Base persistence module for Pepperpy framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, ClassVar

from pepperpy.core.utils.errors import PepperpyError


class PersistenceError(PepperpyError):
    """Persistence error class."""
    pass


T = TypeVar('T', bound='BasePersistence')


class BasePersistence(ABC):
    """Base class for persistence implementations.
    
    This class defines the interface for persistence operations in Pepperpy.
    Persistence implementations are responsible for storing and retrieving
    data with different storage backends and strategies.
    """
    
    _registry: ClassVar[Dict[str, Type['BasePersistence']]] = {}
    
    @classmethod
    def register(cls, name: str) -> Any:
        """Register a persistence class.
        
        Args:
            name: Name to register the persistence under.
            
        Returns:
            Decorator function.
        """
        def decorator(persistence_cls: Type[T]) -> Type[T]:
            cls._registry[name] = persistence_cls
            return persistence_cls
        return decorator
    
    @classmethod
    def get_persistence(cls, name: str) -> Type['BasePersistence']:
        """Get a registered persistence class.
        
        Args:
            name: Name of the persistence.
            
        Returns:
            Persistence class.
            
        Raises:
            ValueError: If persistence is not registered.
        """
        if name not in cls._registry:
            raise ValueError(f"Persistence '{name}' not registered")
        return cls._registry[name]
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize persistence.
        
        Args:
            name: Persistence name
            config: Optional configuration
        """
        if not name:
            raise ValueError("Persistence name cannot be empty")
            
        self._name = name
        self._config = config or {}
        self._initialized = False
        
    @property
    def name(self) -> str:
        """Get persistence name."""
        return self._name
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get persistence configuration."""
        return self._config
        
    @property
    def is_initialized(self) -> bool:
        """Check if persistence is initialized."""
        return self._initialized
        
    async def initialize(self) -> None:
        """Initialize persistence.
        
        This method should be called before using the persistence.
        
        Raises:
            PersistenceError: If initialization fails.
        """
        if self.is_initialized:
            return
            
        try:
            await self._initialize_impl()
            self._initialized = True
        except Exception as e:
            raise PersistenceError(f"Failed to initialize persistence {self.name}: {e}")
            
    async def cleanup(self) -> None:
        """Clean up persistence.
        
        This method should be called when the persistence is no longer needed.
        
        Raises:
            PersistenceError: If cleanup fails.
        """
        if not self.is_initialized:
            return
            
        try:
            await self._cleanup_impl()
            self._initialized = False
        except Exception as e:
            raise PersistenceError(f"Failed to clean up persistence {self.name}: {e}")
            
    def validate(self) -> None:
        """Validate persistence configuration.
        
        This method should be called after initialization to validate
        that the persistence is properly configured.
        
        Raises:
            PersistenceError: If validation fails.
        """
        try:
            self._validate_impl()
        except Exception as e:
            raise PersistenceError(f"Failed to validate persistence {self.name}: {e}")
            
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Initialize persistence implementation.
        
        This method should be implemented by subclasses to perform
        any necessary initialization.
        
        Raises:
            Exception: If initialization fails.
        """
        pass
        
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Clean up persistence implementation.
        
        This method should be implemented by subclasses to perform
        any necessary cleanup.
        
        Raises:
            Exception: If cleanup fails.
        """
        pass
        
    @abstractmethod
    def _validate_impl(self) -> None:
        """Validate persistence implementation.
        
        This method should be implemented by subclasses to validate
        that the persistence is properly configured.
        
        Raises:
            Exception: If validation fails.
        """
        pass
        
    @abstractmethod
    async def store(self, key: str, value: Any) -> None:
        """Store value in persistence.
        
        Args:
            key: Storage key
            value: Value to store
            
        Raises:
            PersistenceError: If value cannot be stored
        """
        pass
        
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from persistence.
        
        Args:
            key: Storage key
            
        Returns:
            Retrieved value or None if not found
            
        Raises:
            PersistenceError: If value cannot be retrieved
        """
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from persistence.
        
        Args:
            key: Storage key
            
        Raises:
            PersistenceError: If value cannot be deleted
        """
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from persistence.
        
        Raises:
            PersistenceError: If values cannot be cleared
        """
        pass
        
    @abstractmethod
    async def list_keys(self) -> List[str]:
        """List all keys in persistence.
        
        Returns:
            List of storage keys
            
        Raises:
            PersistenceError: If keys cannot be listed
        """
        pass
        
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get persistence statistics.
        
        Returns:
            Dictionary containing persistence usage statistics
            
        Raises:
            PersistenceError: If statistics cannot be retrieved
        """
        pass 