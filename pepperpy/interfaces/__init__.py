"""Interfaces module for Pepperpy framework.

This module provides centralized interface definitions for the framework,
promoting loose coupling and dependency inversion.
"""

from typing import Protocol, TypeVar, Dict, Any, Optional, List, Union, AsyncIterator, runtime_checkable
from abc import abstractmethod, ABC
from datetime import datetime

# Type variables
T = TypeVar('T')
ConfigT = TypeVar('ConfigT', bound=Dict[str, Any])

# Core Interfaces
class ConfigurationProvider(Protocol):
    """Protocol defining the interface for configuration providers."""
    
    def load(self) -> ConfigT:
        """Load configuration data."""
        raise NotImplementedError
    
    def save(self, config: ConfigT) -> None:
        """Save configuration data."""
        raise NotImplementedError

class ContextManager(Protocol):
    """Protocol defining the interface for context management."""
    
    def get_context(self) -> Dict[str, Any]:
        """Get the current context."""
        raise NotImplementedError
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """Set the current context."""
        raise NotImplementedError
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update the current context with new values."""
        raise NotImplementedError

class LifecycleManager(Protocol):
    """Protocol defining the interface for lifecycle management."""
    
    async def initialize(self) -> None:
        """Initialize the component."""
        raise NotImplementedError
    
    async def terminate(self) -> None:
        """Terminate the component."""
        raise NotImplementedError
    
    def get_state(self) -> str:
        """Get the current lifecycle state."""
        raise NotImplementedError

# Provider Interfaces
@runtime_checkable
class Lifecycle(Protocol):
    """Lifecycle protocol for components."""
    
    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Return whether the component is initialized."""
        raise NotImplementedError
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component."""
        raise NotImplementedError
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the component."""
        raise NotImplementedError
        
    @abstractmethod
    def validate(self) -> None:
        """Validate component state."""
        raise NotImplementedError

@runtime_checkable
class Provider(Lifecycle, Protocol):
    """Base provider protocol."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name."""
        raise NotImplementedError
        
    @property
    @abstractmethod
    def config(self) -> Dict[str, Any]:
        """Return provider configuration."""
        raise NotImplementedError

class BaseProvider(ABC):
    """Base provider implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        event_bus: Optional[Any] = None,
        monitor: Optional[Any] = None,
        validator: Optional[Any] = None,
    ) -> None:
        """Initialize provider.
        
        Args:
            name: Provider name
            config: Optional configuration
            event_bus: Optional event bus
            monitor: Optional monitor
            validator: Optional validator
        """
        self._name = name
        self._config = config or {}
        self._event_bus = event_bus
        self._monitor = monitor
        self._validator = validator
        self._is_initialized = False
        
    @property
    def name(self) -> str:
        """Return provider name."""
        return self._name
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return provider configuration."""
        return self._config
        
    @property
    def is_initialized(self) -> bool:
        """Return whether provider is initialized."""
        return self._is_initialized
        
    @property
    def event_bus(self) -> Optional[Any]:
        """Return event bus."""
        return self._event_bus
        
    @property
    def monitor(self) -> Optional[Any]:
        """Return monitor."""
        return self._monitor
        
    @property
    def validator(self) -> Optional[Any]:
        """Return validator."""
        return self._validator
        
    async def initialize(self) -> None:
        """Initialize provider."""
        if self.is_initialized:
            return
            
        if self.event_bus:
            await self.event_bus.initialize()
            
        if self.monitor:
            await self.monitor.initialize()
            
        if self.validator:
            await self.validator.initialize()
            
        await self._initialize_impl()
        self._is_initialized = True
        
    async def cleanup(self) -> None:
        """Clean up provider."""
        if not self.is_initialized:
            return
            
        await self._cleanup_impl()
        
        if self.validator:
            await self.validator.cleanup()
            
        if self.monitor:
            await self.monitor.cleanup()
            
        if self.event_bus:
            await self.event_bus.cleanup()
            
        self._is_initialized = False
        
    async def validate(self) -> None:
        """Validate provider state."""
        if not self.name:
            raise ValueError("Empty provider name")
            
        if self.event_bus:
            await self.event_bus.validate()
            
        if self.monitor:
            await self.monitor.validate()
            
        if self.validator:
            await self.validator.validate()
            
        await self._validate_impl()
        
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Initialize implementation."""
        pass
        
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Clean up implementation."""
        pass
        
    async def _validate_impl(self) -> None:
        """Validate implementation."""
        pass

class LLMProvider(Provider, Protocol):
    """Protocol for LLM providers."""
    
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from a prompt."""
        raise NotImplementedError

class VectorStoreProvider(Provider, Protocol):
    """Protocol for vector store providers."""
    
    async def store(self, vectors: Dict[str, Any]) -> None:
        """Store vectors."""
        raise NotImplementedError
    
    async def query(self, query: Any, **kwargs: Any) -> Dict[str, Any]:
        """Query stored vectors."""
        raise NotImplementedError

class EmbeddingProvider(Provider, Protocol):
    """Protocol for embedding providers."""
    
    async def embed(self, text: str) -> Dict[str, Any]:
        """Generate embeddings for text."""
        raise NotImplementedError

# Service Interfaces
class RESTService(Protocol):
    """REST service interface."""
    
    async def handle_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Handle REST request."""
        raise NotImplementedError

class WebSocketService(Protocol):
    """WebSocket service interface."""
    
    async def handle_message(
        self,
        message: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle WebSocket message."""
        raise NotImplementedError

# Data Interfaces
class Embeddable(Protocol):
    """Protocol for objects that can be embedded."""
    
    @abstractmethod
    def to_embedding(self) -> List[float]:
        """Convert object to embedding vector."""
        raise NotImplementedError
        
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return embedding dimension."""
        raise NotImplementedError

class Chunkable(Protocol[T]):
    """Protocol for objects that can be chunked."""
    
    @abstractmethod
    def chunk(
        self,
        chunk_size: int,
        overlap: int = 0
    ) -> List[T]:
        """Split object into chunks."""
        raise NotImplementedError

class SimilarityComparable(Protocol):
    """Protocol for objects that can be compared by similarity."""
    
    @abstractmethod
    def similarity(self, other: Any) -> float:
        """Calculate similarity with another object."""
        raise NotImplementedError

class Storable(Protocol):
    """Protocol for objects that can be stored."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Return object ID."""
        raise NotImplementedError
        
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return object metadata."""
        raise NotImplementedError

class Indexable(Storable, Protocol):
    """Protocol for objects that can be indexed."""
    
    @property
    @abstractmethod
    def index_key(self) -> str:
        """Return index key."""
        raise NotImplementedError
        
    @property
    @abstractmethod
    def index_value(self) -> Any:
        """Return index value."""
        raise NotImplementedError

class Cacheable(Protocol):
    """Protocol for objects that can be cached."""
    
    @property
    @abstractmethod
    def cache_key(self) -> str:
        """Return cache key."""
        raise NotImplementedError
        
    @property
    @abstractmethod
    def ttl(self) -> Optional[int]:
        """Return time-to-live in seconds."""
        raise NotImplementedError

class StorageBackend(Protocol[T]):
    """Protocol for objects that can be used as storage backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Get value by key."""
        raise NotImplementedError
        
    @abstractmethod
    async def set(self, key: str, value: T) -> None:
        """Set value for key."""
        raise NotImplementedError
        
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value by key."""
        raise NotImplementedError
        
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        raise NotImplementedError
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values."""
        raise NotImplementedError

# Event Interfaces
class EventFilter(Protocol):
    """Event filter protocol."""
    
    def matches(self, event: Any) -> bool:
        """Check if event matches filter."""
        raise NotImplementedError

class EventTransformer(Protocol):
    """Event transformer protocol."""
    
    def transform(self, event: Any) -> Any:
        """Transform event."""
        raise NotImplementedError

# Object Interfaces
class PepperpyObject(Protocol):
    """Base protocol for all Pepperpy objects."""
    
    @property
    def name(self) -> str:
        """Get object name."""
        raise NotImplementedError

class DictInitializable(Protocol):
    """Protocol for objects that can be initialized from a dictionary."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DictInitializable":
        """Initialize object from dictionary."""
        raise NotImplementedError
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary."""
        raise NotImplementedError

class Validatable(Protocol):
    """Protocol for objects that can be validated."""
    
    def validate(self) -> None:
        """Validate object state."""
        raise NotImplementedError

# Tool Interfaces
class Tool(Provider, Protocol):
    """Protocol for tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get tool name."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get tool description."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Get initialization status."""
        raise NotImplementedError
    
    @abstractmethod
    async def execute(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute tool.
        
        Args:
            input_data: Input data
            context: Optional execution context
            
        Returns:
            Tool result
        """
        raise NotImplementedError

class ToolManager(Provider, Protocol):
    """Protocol for tool managers."""
    
    @abstractmethod
    def add_tool(self, tool: Tool) -> None:
        """Add tool.
        
        Args:
            tool: Tool to add
        """
        raise NotImplementedError
    
    @abstractmethod
    def remove_tool(self, name: str) -> None:
        """Remove tool.
        
        Args:
            name: Tool name
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_tool(self, name: str) -> Tool:
        """Get tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance
        """
        raise NotImplementedError
    
    @abstractmethod
    async def execute_tool(
        self,
        name: str,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute tool.
        
        Args:
            name: Tool name
            input_data: Input data
            context: Optional execution context
            
        Returns:
            Tool result
        """
        raise NotImplementedError

# Export all interfaces
__all__ = [
    # Core Interfaces
    'ConfigurationProvider',
    'ContextManager',
    'LifecycleManager',
    # Provider Interfaces
    'Provider',
    'LLMProvider',
    'VectorStoreProvider',
    'EmbeddingProvider',
    # Service Interfaces
    'RESTService',
    'WebSocketService',
    # Data Interfaces
    'Embeddable',
    'Chunkable',
    'SimilarityComparable',
    'Storable',
    'Indexable',
    'Cacheable',
    'StorageBackend',
    # Event Interfaces
    'EventFilter',
    'EventTransformer',
    # Object Interfaces
    'PepperpyObject',
    'DictInitializable',
    'Validatable',
    # Tool Interfaces
    'Tool',
    'ToolManager',
] 