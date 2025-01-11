"""Base classes for embedding capabilities."""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union

from pepperpy_ai.capabilities.base import BaseCapability, CapabilityConfig


class EmbeddingConfig(CapabilityConfig):
    """Configuration for embedding capabilities."""

    model_name: str
    dimension: int
    normalize: bool = True
    batch_size: int = 32
    metadata: Optional[Dict[str, Any]] = None


class BaseEmbedding(BaseCapability):
    """Base class for embedding implementations."""

    def __init__(self, config: EmbeddingConfig) -> None:
        """Initialize the embedding capability.

        Args:
            config: The embedding configuration.
        """
        super().__init__(config)
        self.config = config

    @abstractmethod
    async def encode(
        self, texts: Union[str, List[str]], batch_size: Optional[int] = None
    ) -> Union[List[float], List[List[float]]]:
        """Encode text(s) into embeddings.

        Args:
            texts: A single text or list of texts to encode.
            batch_size: Optional batch size for processing. Defaults to config value.

        Returns:
            A single embedding vector or list of embedding vectors.
        """
        pass

    @abstractmethod
    async def encode_queries(
        self, queries: Union[str, List[str]], batch_size: Optional[int] = None
    ) -> Union[List[float], List[List[float]]]:
        """Encode query text(s) into embeddings.

        Some models have different encodings for queries vs documents.

        Args:
            queries: A single query or list of queries to encode.
            batch_size: Optional batch size for processing. Defaults to config value.

        Returns:
            A single embedding vector or list of embedding vectors.
        """
        pass

    @abstractmethod
    async def similarity(
        self, embeddings1: List[float], embeddings2: List[float]
    ) -> float:
        """Calculate similarity between two embeddings.

        Args:
            embeddings1: First embedding vector.
            embeddings2: Second embedding vector.

        Returns:
            Similarity score between the embeddings.
        """
        pass

    @abstractmethod
    async def bulk_similarity(
        self,
        query_embeddings: Union[List[float], List[List[float]]],
        document_embeddings: List[List[float]],
    ) -> Union[List[float], List[List[float]]]:
        """Calculate similarities between query and document embeddings.

        Args:
            query_embeddings: Single or multiple query embeddings.
            document_embeddings: List of document embeddings.

        Returns:
            Similarity scores for each query-document pair.
        """
        pass 