"""Vector support for memory operations."""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from ..common.errors import PepperpyError
from ..data.vector import VectorIndex
from ..data.vector.embeddings import EmbeddingManager
from ..models.types import Message


logger = logging.getLogger(__name__)


class VectorError(PepperpyError):
    """Vector error."""
    pass


class VectorSupport:
    """Vector support for memory operations."""
    
    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        vector_index: VectorIndex,
        namespace: str = "default",
        min_score: float = 0.0,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize vector support.
        
        Args:
            embedding_manager: Embedding manager
            vector_index: Vector index
            namespace: Storage namespace (default: default)
            min_score: Minimum relevance score (default: 0.0)
            config: Optional configuration
        """
        self._embedding_manager = embedding_manager
        self._vector_index = vector_index
        self._namespace = namespace
        self._min_score = min_score
        self._config = config or {}
        
    @property
    def namespace(self) -> str:
        """Return storage namespace."""
        return self._namespace
        
    async def add_message(self, message: Message) -> None:
        """Add message to vector index.
        
        Args:
            message: Message to add
            
        Raises:
            VectorError: If message cannot be added
        """
        try:
            # Get message embedding
            embedding = await self._get_embedding(message.content)
            
            # Add to vector index
            await self._vector_index.add(
                vector=embedding,
                metadata={
                    "message_id": message.message_id,
                    "namespace": self._namespace,
                    **message.metadata,
                },
            )
            
        except Exception as e:
            raise VectorError(f"Failed to add message: {e}") from e
            
    async def search_messages(
        self,
        query: str,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float]]:
        """Search messages by content.
        
        Args:
            query: Search query
            limit: Optional result limit
            filters: Optional metadata filters
            
        Returns:
            List of (message ID, score) tuples
            
        Raises:
            VectorError: If messages cannot be searched
        """
        try:
            # Get query embedding
            embedding = await self._get_embedding(query)
            
            # Add namespace filter
            if filters is None:
                filters = {}
            filters["namespace"] = self._namespace
            
            # Search vector index
            results = await self._vector_index.search(
                query=embedding,
                limit=limit,
                filters=filters,
                min_score=self._min_score,
            )
            
            # Extract message IDs and scores
            return [
                (result.metadata["message_id"], result.score)
                for result in results
            ]
            
        except Exception as e:
            raise VectorError(f"Failed to search messages: {e}") from e
            
    async def clear(self) -> None:
        """Clear vector index.
        
        Raises:
            VectorError: If vector index cannot be cleared
        """
        try:
            await self._vector_index.delete(
                filters={"namespace": self._namespace},
            )
            
        except Exception as e:
            raise VectorError(f"Failed to clear vector index: {e}") from e
            
    async def _get_embedding(self, text: str) -> NDArray[np.float32]:
        """Get text embedding.
        
        Args:
            text: Text to embed
            
        Returns:
            Text embedding
            
        Raises:
            VectorError: If text cannot be embedded
        """
        try:
            return await self._embedding_manager.get_embedding(text)
            
        except Exception as e:
            raise VectorError(f"Failed to get embedding: {e}") from e
            
    def validate(self) -> None:
        """Validate vector support state."""
        if not self._namespace:
            raise ValueError("Storage namespace cannot be empty")
            
        if not self._embedding_manager:
            raise ValueError("Embedding manager not provided")
            
        if not self._vector_index:
            raise ValueError("Vector index not provided")
