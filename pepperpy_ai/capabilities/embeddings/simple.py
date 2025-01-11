"""Simple embedding implementation using sentence transformers."""

from typing import List, Optional, Union

from pepperpy_ai.capabilities.embeddings.base import BaseEmbedding, EmbeddingConfig
from pepperpy_ai.exceptions import DependencyError


class SimpleEmbedding(BaseEmbedding):
    """A simple embedding implementation using sentence transformers."""

    def __init__(self, config: EmbeddingConfig) -> None:
        """Initialize SimpleEmbedding.

        Args:
            config: The embedding configuration.
        """
        super().__init__(config)
        self._model = None
        self._np = None
        self._sentence_transformers = None

    async def initialize(self) -> None:
        """Initialize the embedding system."""
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
            self._np = np
            self._sentence_transformers = SentenceTransformer
            self._model = SentenceTransformer(self.config.model_name)
        except ImportError as e:
            raise DependencyError(
                "Missing required dependencies for embeddings: numpy, sentence-transformers",
                package="numpy, sentence-transformers"
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._model = None
        self._np = None
        self._sentence_transformers = None

    async def encode(
        self, texts: Union[str, List[str]], batch_size: Optional[int] = None
    ) -> Union[List[float], List[List[float]]]:
        """Encode text(s) into embeddings.

        Args:
            texts: A single text or list of texts to encode.
            batch_size: Optional batch size for processing.

        Returns:
            A single embedding vector or list of embedding vectors.
        """
        if not self._model:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        batch_size = batch_size or self.config.batch_size
        texts_list = [texts] if isinstance(texts, str) else texts
        embeddings = self._model.encode(
            texts_list,
            batch_size=batch_size,
            convert_to_tensor=False,
            normalize_embeddings=self.config.normalize,
        )

        if isinstance(texts, str):
            return embeddings[0].tolist()
        return [emb.tolist() for emb in embeddings]

    async def encode_queries(
        self, queries: Union[str, List[str]], batch_size: Optional[int] = None
    ) -> Union[List[float], List[List[float]]]:
        """Encode query text(s) into embeddings.

        Args:
            queries: A single query or list of queries to encode.
            batch_size: Optional batch size for processing.

        Returns:
            A single embedding vector or list of embedding vectors.
        """
        # For simple implementation, query encoding is same as document encoding
        return await self.encode(queries, batch_size)

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
        if not self._np:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        # Convert to numpy arrays for efficient computation
        emb1 = self._np.array(embeddings1)
        emb2 = self._np.array(embeddings2)

        # Normalize if needed
        if self.config.normalize:
            emb1 = emb1 / self._np.linalg.norm(emb1)
            emb2 = emb2 / self._np.linalg.norm(emb2)

        # Compute cosine similarity
        return float(self._np.dot(emb1, emb2))

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
        if not self._np:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        # Convert to numpy arrays
        if isinstance(query_embeddings[0], float):
            # Single query
            query_array = self._np.array([query_embeddings])
            single_query = True
        else:
            # Multiple queries
            query_array = self._np.array(query_embeddings)
            single_query = False

        doc_array = self._np.array(document_embeddings)

        # Normalize if needed
        if self.config.normalize:
            query_array = query_array / self._np.linalg.norm(query_array, axis=1)[:, self._np.newaxis]
            doc_array = doc_array / self._np.linalg.norm(doc_array, axis=1)[:, self._np.newaxis]

        # Compute similarities
        similarities = self._np.dot(query_array, doc_array.T)

        if single_query:
            return similarities[0].tolist()
        return similarities.tolist() 