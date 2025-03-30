"""Local embeddings provider plugin using sentence-transformers."""

import os
from typing import Any, Dict, List, Optional, Union, cast

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from pepperpy.core import ProviderError
from pepperpy.embeddings import EmbeddingProvider
from pepperpy.plugin import ProviderPlugin


class LocalProvider(EmbeddingProvider, ProviderPlugin):
    """Local embeddings provider using sentence-transformers."""

    # Auto-bound attributes from plugin.yaml
    model_name: str
    device: Optional[str]
    cache_dir: Optional[str]
    model: Optional[SentenceTransformer]

    async def initialize(self) -> None:
        """Initialize the model."""
        if self.initialized:
            return

        try:
            # Set default device if not provided
            if not self.device:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

            # Set default cache directory if not provided
            if not self.cache_dir:
                self.cache_dir = os.path.expanduser(
                    "~/.cache/torch/sentence_transformers"
                )

            os.makedirs(self.cache_dir, exist_ok=True)

            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=self.cache_dir,
                device=self.device,
            )
        except Exception as e:
            raise ProviderError(
                f"Failed to initialize sentence-transformers model: {e}"
            ) from e

        self.initialized = True

    async def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for the given text.

        Args:
            text: Text or list of texts to embed

        Returns:
            List of embeddings vectors
        """
        if not self.initialized or not self.model:
            await self.initialize()

        if isinstance(text, str):
            text = [text]

        # At this point self.model is guaranteed to be initialized
        model = cast(SentenceTransformer, self.model)

        try:
            embeddings = model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        except Exception as e:
            raise ProviderError(f"Failed to generate embeddings: {e}") from e

        # Convert to list of lists and ensure float type
        return embeddings.astype(np.float32).tolist()

    async def embed_query(self, text: str) -> List[float]:
        """Generate embeddings for a query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        embeddings = await self.embed_text(text)
        return embeddings[0]

    def get_embedding_function(self) -> Any:
        """Get a function that can be used by vector stores.

        Returns:
            A callable that generates embeddings
        """

        async def embedding_function(texts: List[str]) -> List[List[float]]:
            return await self.embed_text(texts)

        return embedding_function

    async def get_dimensions(self) -> int:
        """Get the dimensionality of the embeddings.

        Returns:
            The number of dimensions in the embeddings
        """
        if not self.initialized or not self.model:
            await self.initialize()

        # At this point self.model is guaranteed to be initialized
        model = cast(SentenceTransformer, self.model)
        return model.get_sentence_embedding_dimension()

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return {
            "model": self.model_name,
            "device": self.device,
            "cache_dir": self.cache_dir,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {
            "models": [
                "all-MiniLM-L6-v2",
                "all-mpnet-base-v2",
                "multi-qa-mpnet-base-dot-v1",
            ],
            "supports_batch": True,
            "supports_async": False,  # sentence-transformers is sync
            "supports_gpu": torch.cuda.is_available(),
            "device": self.device,
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.model:
            # Free GPU memory if using CUDA
            if self.device == "cuda":
                torch.cuda.empty_cache()
            self.model = None
