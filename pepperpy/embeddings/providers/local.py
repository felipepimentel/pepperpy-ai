"""Local embedding provider implementation.

This module provides a local implementation of the embedding provider interface,
using sentence-transformers for document embeddings.
"""

from typing import Any, Dict, List, Optional, Sequence, Union

from ..base import EmbeddingProvider
from ..errors import EmbeddingError


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local implementation of the embedding provider interface using sentence-transformers."""

    name = "local"

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        normalize_embeddings: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize the Local embedding provider.

        Args:
            model: Model name from sentence-transformers (default: all-MiniLM-L6-v2)
            device: Device to run model on (default: cpu)
            normalize_embeddings: Whether to normalize embeddings (default: True)
            **kwargs: Additional configuration options

        Raises:
            EmbeddingError: If required dependencies are not installed
        """
        super().__init__(name=name, **kwargs)
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise EmbeddingError(
                "Local provider requires sentence-transformers. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model
        self.device = device
        self.normalize = normalize_embeddings
        self.model = SentenceTransformer(model, device=device)
        self.dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "multi-qa-MiniLM-L6-cos-v1": 384,
        }

    async def embed_text(
        self,
        text: Union[str, List[str]],
        **kwargs: Any,
    ) -> Union[List[float], List[List[float]]]:
        """Convert text to vector embeddings."""
        # Convert single text to list
        texts = [text] if isinstance(text, str) else text

        # Get embeddings
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.normalize,
            **kwargs,
        ).tolist()

        # Return single vector for single text
        return embeddings[0] if isinstance(text, str) else embeddings

    async def embed_documents(
        self,
        documents: Sequence[Dict[str, Any]],
        text_field: str = "content",
        **kwargs: Any,
    ) -> List[List[float]]:
        """Convert documents to vector embeddings."""
        # Extract text from documents
        texts = []
        for doc in documents:
            if text_field not in doc:
                raise EmbeddingError(f"Document missing {text_field} field")
            texts.append(doc[text_field])

        # Get embeddings
        return await self.embed_text(texts, **kwargs)

    def get_dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.dimensions.get(self.model_name, 384)

    def get_model_name(self) -> str:
        """Get embedding model name."""
        return self.model_name

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Local embedding provider capabilities."""
        return {
            "supported_models": list(self.dimensions.keys()),
            "max_tokens": None,  # No token limit
            "supports_batch": True,
            "dimensions": self.dimensions,
        }
