"""Base vector store provider implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, ClassVar

from ...interfaces import VectorStoreProvider

logger = logging.getLogger(__name__)

class BaseVectorStoreProvider(ABC, VectorStoreProvider):
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
        def decorator(provider_cls: Type['BaseVectorStoreProvider']) -> Type['BaseVectorStoreProvider']:
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
        """Initialize the provider.
        
        Args:
            config: Provider configuration.
        """
        self.config = config
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the provider.
        
        Raises:
            ValueError: If initialization fails.
        """
        if self.is_initialized:
            return
            
        try:
            await self._initialize_impl()
            self.is_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize provider: {str(e)}")
            await self.cleanup()
            raise ValueError(f"Provider initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        try:
            await self._cleanup_impl()
        finally:
            self.is_initialized = False
    
    async def store(self, vectors: Dict[str, Any]) -> None:
        """Store vectors.
        
        Args:
            vectors: Vector data to store.
            
        Raises:
            ValueError: If the provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        await self._store_impl(vectors)
    
    async def query(self, query: Any, **kwargs: Any) -> Dict[str, Any]:
        """Query stored vectors.
        
        Args:
            query: Query vector or parameters.
            **kwargs: Additional query parameters.
            
        Returns:
            Query results.
            
        Raises:
            ValueError: If the provider is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        return await self._query_impl(query, **kwargs)
    
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Implementation-specific initialization."""
        raise NotImplementedError
    
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Implementation-specific cleanup."""
        raise NotImplementedError
    
    @abstractmethod
    async def _store_impl(self, vectors: Dict[str, Any]) -> None:
        """Implementation-specific vector storage.
        
        Args:
            vectors: Vector data to store.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def _query_impl(self, query: Any, **kwargs: Any) -> Dict[str, Any]:
        """Implementation-specific vector querying.
        
        Args:
            query: Query vector or parameters.
            **kwargs: Additional query parameters.
            
        Returns:
            Query results.
        """
        raise NotImplementedError
    
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