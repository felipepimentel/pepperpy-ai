"""Base memory provider implementation for Pepperpy framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, ClassVar

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.providers.base import Provider


class MemoryError(PepperpyError):
    """Memory provider error."""
    pass


T = TypeVar('T', bound='BaseMemoryProvider')


class BaseMemoryProvider(ABC, Provider):
    """Base memory provider implementation.
    
    This class defines the interface for memory providers in Pepperpy.
    Memory providers are responsible for storing and retrieving data
    with different persistence and retrieval strategies.
    """
    
    _registry: ClassVar[Dict[str, Type['BaseMemoryProvider']]] = {}
    
    @classmethod
    def register(cls, name: str) -> Any:
        """Register a provider class.
        
        Args:
            name: Name to register the provider under.
            
        Returns:
            Decorator function.
        """
        def decorator(provider_cls: Type[T]) -> Type[T]:
            cls._registry[name] = provider_cls
            return provider_cls
        return decorator
    
    @classmethod
    def get_provider(cls, name: str) -> Type['BaseMemoryProvider']:
        """Get a registered provider class.
        
        Args:
            name: Name of the provider.
            
        Returns:
            Provider class.
            
        Raises:
            ValueError: If provider is not registered.
        """
        if name not in cls._registry:
            raise ValueError(f"Provider '{name}' not registered")
        return cls._registry[name]
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider.
        
        Args:
            name: Provider name
            config: Optional configuration
        """
        if not name:
            raise ValueError("Provider name cannot be empty")
            
        self._name = name
        self._config = config or {}
        self._initialized = False
        
    @property
    def name(self) -> str:
        """Get provider name."""
        return self._name
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get provider configuration."""
        return self._config
        
    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized
        
    async def initialize(self) -> None:
        """Initialize provider.
        
        This method should be called before using the provider.
        
        Raises:
            MemoryError: If initialization fails.
        """
        if self.is_initialized:
            return
            
        try:
            await self._initialize_impl()
            self._initialized = True
        except Exception as e:
            raise MemoryError(f"Failed to initialize provider {self.name}: {e}")
            
    async def cleanup(self) -> None:
        """Clean up provider.
        
        This method should be called when the provider is no longer needed.
        
        Raises:
            MemoryError: If cleanup fails.
        """
        if not self.is_initialized:
            return
            
        try:
            await self._cleanup_impl()
            self._initialized = False
        except Exception as e:
            raise MemoryError(f"Failed to clean up provider {self.name}: {e}")
            
    def validate(self) -> None:
        """Validate provider configuration.
        
        This method should be called after initialization to validate
        that the provider is properly configured.
        
        Raises:
            MemoryError: If validation fails.
        """
        try:
            self._validate_impl()
        except Exception as e:
            raise MemoryError(f"Failed to validate provider {self.name}: {e}")
            
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Initialize provider implementation.
        
        This method should be implemented by subclasses to perform
        any necessary initialization.
        
        Raises:
            Exception: If initialization fails.
        """
        pass
        
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Clean up provider implementation.
        
        This method should be implemented by subclasses to perform
        any necessary cleanup.
        
        Raises:
            Exception: If cleanup fails.
        """
        pass
        
    @abstractmethod
    def _validate_impl(self) -> None:
        """Validate provider implementation.
        
        This method should be implemented by subclasses to validate
        that the provider is properly configured.
        
        Raises:
            Exception: If validation fails.
        """
        pass
        
    @abstractmethod
    async def store(self, key: str, value: Any) -> None:
        """Store value in memory.
        
        Args:
            key: Storage key
            value: Value to store
            
        Raises:
            MemoryError: If value cannot be stored
        """
        pass
        
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from memory.
        
        Args:
            key: Storage key
            
        Returns:
            Retrieved value or None if not found
            
        Raises:
            MemoryError: If value cannot be retrieved
        """
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from memory.
        
        Args:
            key: Storage key
            
        Raises:
            MemoryError: If value cannot be deleted
        """
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from memory.
        
        Raises:
            MemoryError: If memory cannot be cleared
        """
        pass
        
    @abstractmethod
    async def list_keys(self) -> List[str]:
        """List all keys in memory.
        
        Returns:
            List of storage keys
            
        Raises:
            MemoryError: If keys cannot be listed
        """
        pass

    @abstractmethod
    async def add(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Add a memory entry.

        Args:
            key: Memory entry key
            value: Memory entry value
            metadata: Optional metadata for the entry
            **kwargs: Additional provider-specific parameters

        Raises:
            ProviderError: If adding memory entry fails
        """
        pass

    @abstractmethod
    async def get(
        self,
        key: str,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Get a memory entry.

        Args:
            key: Memory entry key
            **kwargs: Additional provider-specific parameters

        Returns:
            Memory entry with value and metadata if found, None otherwise

        Raises:
            ProviderError: If retrieving memory entry fails
        """
        pass

    @abstractmethod
    async def update(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> bool:
        """Update a memory entry.

        Args:
            key: Memory entry key
            value: New memory entry value
            metadata: Optional new metadata
            **kwargs: Additional provider-specific parameters

        Returns:
            True if successful, False if entry not found

        Raises:
            ProviderError: If updating memory entry fails
        """
        pass

    @abstractmethod
    async def list(
        self,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """List memory entries.

        Args:
            filter: Optional metadata filter
            **kwargs: Additional provider-specific parameters

        Returns:
            List of memory entries with values and metadata

        Raises:
            ProviderError: If listing memory entries fails
        """
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory provider statistics.

        Returns:
            Dictionary containing memory usage statistics

        Raises:
            ProviderError: If retrieving statistics fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Search memory entries.

        Args:
            query: Search query string
            filter: Optional metadata filter
            limit: Maximum number of results to return
            **kwargs: Additional provider-specific parameters

        Returns:
            List of matching memory entries with values and metadata

        Raises:
            ProviderError: If searching memory entries fails
        """
        pass

    @abstractmethod
    async def add_message(self, message: Message) -> None:
        """Add a message to memory.
        
        Args:
            message: Message to add.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
    
    @abstractmethod
    async def get_messages(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        role: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get messages from memory.
        
        Args:
            start_time: Optional start time filter.
            end_time: Optional end time filter.
            role: Optional role filter.
            limit: Optional limit on number of messages.
            
        Returns:
            List of messages.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
    
    @abstractmethod
    async def clear_messages(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        role: Optional[str] = None
    ) -> None:
        """Clear messages from memory.
        
        Args:
            start_time: Optional start time filter.
            end_time: Optional end time filter.
            role: Optional role filter.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
    
    @abstractmethod
    async def search_messages(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Search messages in memory.
        
        Args:
            query: Search query.
            limit: Optional limit on number of results.
            
        Returns:
            List of matching messages.
            
        Raises:
            ValueError: If provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized") 