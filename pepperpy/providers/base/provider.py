"""
Base provider interface and abstract classes.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pepperpy.core.utils.errors import ProviderError


class BaseProvider(ABC):
    """Base class for all providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the provider.
        
        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.
        
        This method should be called before using the provider.
        It should handle any setup required by the provider.
        """
        self._initialized = True

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider.
        
        This method should be called when the provider is no longer needed.
        It should handle cleanup of any resources.
        """
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure the provider is initialized before use."""
        if not self._initialized:
            raise ProviderError("Provider not initialized. Call initialize() first.")

    @property
    def is_initialized(self) -> bool:
        """Check if the provider is initialized."""
        return self._initialized


class LLMProvider(BaseProvider):
    """Base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from a prompt.
        
        Args:
            prompt: The input prompt.
            **kwargs: Additional provider-specific arguments.
            
        Returns:
            The generated text.
        """
        raise NotImplementedError


class VectorStoreProvider(BaseProvider):
    """Base class for vector store providers."""

    @abstractmethod
    async def store(self, vectors: list[float], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store vectors in the database.
        
        Args:
            vectors: List of vectors to store.
            metadata: Optional metadata associated with the vectors.
            
        Returns:
            ID of the stored vectors.
        """
        raise NotImplementedError

    @abstractmethod
    async def search(self, query_vector: list[float], k: int = 5) -> list[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Vector to search for.
            k: Number of results to return.
            
        Returns:
            List of similar vectors with their metadata.
        """
        raise NotImplementedError


class EmbeddingProvider(BaseProvider):
    """Base class for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text.
        
        Args:
            text: Text to generate embeddings for.
            
        Returns:
            Vector representation of the text.
        """
        raise NotImplementedError


class MemoryProvider(BaseProvider):
    """Base class for memory providers."""

    @abstractmethod
    async def store(self, key: str, value: Any) -> None:
        """Store a value in memory.
        
        Args:
            key: Key to store the value under.
            value: Value to store.
        """
        raise NotImplementedError

    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory.
        
        Args:
            key: Key to retrieve.
            
        Returns:
            The stored value, or None if not found.
        """
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        """Clear all stored values."""
        raise NotImplementedError 