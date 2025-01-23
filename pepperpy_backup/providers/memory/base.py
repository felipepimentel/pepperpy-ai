"""Base interface for memory providers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, TypeVar, ClassVar
from datetime import datetime

T = TypeVar('T', bound='BaseMemoryProvider')

class Message:
    """Message class for storing conversation history."""
    
    def __init__(
        self,
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Initialize a message.
        
        Args:
            content: Message content.
            role: Role of the message sender (e.g. "user", "assistant").
            metadata: Optional metadata dictionary.
            timestamp: Optional message timestamp.
        """
        self.content = content
        self.role = role
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary.
        
        Returns:
            Dictionary representation of the message.
        """
        return {
            "content": self.content,
            "role": self.role,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary.
        
        Args:
            data: Dictionary representation of the message.
            
        Returns:
            Message instance.
        """
        return cls(
            content=data["content"],
            role=data["role"],
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )

class BaseMemoryProvider(ABC):
    """Base class for memory providers."""
    
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
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the memory provider.
        
        Args:
            config: Configuration dictionary for the provider.
        """
        self.config = config
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider.
        
        Returns:
            True if initialization was successful.
            
        Raises:
            ValueError: If initialization fails.
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources used by the provider."""
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