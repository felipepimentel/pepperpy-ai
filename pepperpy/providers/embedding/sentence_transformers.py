"""
Sentence Transformers embedding provider implementation.
"""
from typing import Any, Dict, List, Optional, Union, cast

import numpy as np
from sentence_transformers import SentenceTransformer

from pepperpy.core.utils.errors import ProviderError
from pepperpy.providers.embedding.base import EmbeddingProvider


class SentenceTransformersProvider(EmbeddingProvider):
    """Sentence Transformers embedding provider implementation."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Sentence Transformers provider.

        Args:
            model_name: Name of the model to use.
            device: Device to use (e.g., "cpu", "cuda").
            **kwargs: Additional configuration parameters.
        """
        super().__init__({"model_name": model_name, "device": device, **kwargs})
        self._model: Optional[SentenceTransformer] = None
        self._model_name = model_name
        self._device = device

    async def initialize(self) -> None:
        """Initialize the Sentence Transformers model.

        Raises:
            ProviderError: If initialization fails.
        """
        try:
            await self.validate_config()
            self._model = SentenceTransformer(
                self._model_name,
                device=self._device if self._device else "cpu",
            )
            self._initialized = True
        except Exception as e:
            raise ProviderError(
                f"Failed to initialize Sentence Transformers provider: {str(e)}"
            ) from e

    async def validate_config(self) -> None:
        """Validate the provider configuration.

        Raises:
            ProviderError: If configuration is invalid.
        """
        if not self.config.get("model_name"):
            raise ProviderError("Model name is required")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        self._model = None
        self._initialized = False

    async def embed_text(
        self,
        text: Union[str, List[str]],
        **kwargs: Any,
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text.

        Args:
            text: Input text or list of texts.
            **kwargs: Additional provider-specific parameters.

        Returns:
            A single embedding vector or list of embedding vectors.

        Raises:
            ProviderError: If embedding generation fails.
        """
        if not self._model or not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            embeddings = self._model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,
                **kwargs,
            )
            if isinstance(text, str):
                return cast(List[float], embeddings.tolist())
            return cast(List[List[float]], embeddings.tolist())
        except Exception as e:
            raise ProviderError(f"Failed to generate embeddings: {str(e)}") from e

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        **kwargs: Any,
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of input texts.
            batch_size: Optional batch size for processing.
            **kwargs: Additional provider-specific parameters.

        Returns:
            List of embedding vectors.

        Raises:
            ProviderError: If batch embedding generation fails.
        """
        if not self._model or not self._initialized:
            raise ProviderError("Provider not initialized")

        try:
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size or 32,
                convert_to_numpy=True,
                normalize_embeddings=True,
                **kwargs,
            )
            return cast(List[List[float]], embeddings.tolist())
        except Exception as e:
            raise ProviderError(f"Failed to generate batch embeddings: {str(e)}") from e

    async def get_embedding_dim(self) -> int:
        """Get the dimensionality of the embeddings.

        Returns:
            The number of dimensions in the embedding vectors.

        Raises:
            ProviderError: If retrieving embedding dimension fails.
        """
        if not self._model or not self._initialized:
            raise ProviderError("Provider not initialized")

        return self._model.get_sentence_embedding_dimension()

    async def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
        metric: str = "cosine",
    ) -> float:
        """Calculate similarity between two embeddings.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.
            metric: Similarity metric to use (e.g., "cosine", "euclidean", "dot").

        Returns:
            Similarity score between the embeddings.

        Raises:
            ProviderError: If similarity calculation fails.
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            if metric == "cosine":
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                return float(np.dot(vec1, vec2) / (norm1 * norm2))
            elif metric == "euclidean":
                return float(-np.linalg.norm(vec1 - vec2))
            elif metric == "dot":
                return float(np.dot(vec1, vec2))
            else:
                raise ProviderError(f"Unsupported similarity metric: {metric}")
        except Exception as e:
            raise ProviderError(f"Failed to calculate similarity: {str(e)}") from e

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current embedding model.

        Returns:
            A dictionary containing model information.

        Raises:
            ProviderError: If retrieving model info fails.
        """
        if not self._model or not self._initialized:
            raise ProviderError("Provider not initialized")

        return {
            "name": self._model_name,
            "provider": "sentence_transformers",
            "dimension": await self.get_embedding_dim(),
            "device": self._device or "cpu",
            "capabilities": {
                "batch_processing": True,
                "normalization": True,
                "similarity_metrics": ["cosine", "euclidean", "dot"],
            },
        } 