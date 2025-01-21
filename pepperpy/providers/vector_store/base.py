"""Base interface for vector store providers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, TypeVar, ClassVar

T = TypeVar('T', bound='BaseVectorStoreProvider')

class BaseVectorStoreProvider(ABC):
    """Base class for vector store providers."""
    
    _registry: ClassVar[Dict[str, Type['BaseVectorStoreProvider']]] = {}
    
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
    def get_provider(cls, name: str) -> Type['BaseVectorStoreProvider']:
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
        """Initialize the vector store provider.
        
        Args:
            config: Configuration dictionary for the provider.
        """
        self.config = config
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider resources."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        pass
    
    @abstractmethod
    async def add_vectors(
        self, 
        vectors: List[List[float]], 
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add vectors to the store.
        
        Args:
            vectors: List of vectors to add.
            metadata: Optional metadata for each vector.
            
        Returns:
            List of IDs for the added vectors.
        """
        pass
    
    @abstractmethod
    async def search(
        self, 
        query_vector: List[float], 
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Vector to search for.
            k: Number of results to return.
            filter_metadata: Optional metadata filters.
            
        Returns:
            List of results with their metadata and scores.
        """
        pass
    
    @abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        """Delete vectors from the store.
        
        Args:
            ids: List of vector IDs to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a vector by its ID.
        
        Args:
            id: Vector ID.
            
        Returns:
            Vector data with metadata if found, None otherwise.
        """
        pass
    
    @abstractmethod
    async def update_metadata(self, id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a vector.
        
        Args:
            id: Vector ID.
            metadata: New metadata.
            
        Returns:
            True if successful, False otherwise.
        """
        pass 