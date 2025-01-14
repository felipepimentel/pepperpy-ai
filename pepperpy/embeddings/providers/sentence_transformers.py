"""Sentence transformers embeddings provider module."""

from collections.abc import Sequence
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from pepperpy.embeddings.base import BaseEmbeddingsProvider
from pepperpy.exceptions import DependencyError, ProviderError
from pepperpy.types import CapabilityConfig
from pepperpy.utils.dependencies import check_dependency


class SentenceTransformersProvider(BaseEmbeddingsProvider):
    """Sentence transformers embeddings provider."""

    def __init__(self, config: CapabilityConfig) -> None:
        """Initialize sentence transformers provider.

        Args:
            config: Provider configuration.

        Raises:
            DependencyError: If sentence-transformers is not installed.
        """
        super().__init__(config)
        self._model = None

    async def initialize(self) -> None:
        """Initialize provider.

        Raises:
            DependencyError: If sentence-transformers is not installed.
        """
        if not self.is_initialized:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as err:
                raise DependencyError(
                    "sentence-transformers is required for "
                    "SentenceTransformersProvider",
                    package="sentence-transformers",
                ) from err

            model_name = self.config.model or "all-MiniLM-L6-v2"
            self._model = SentenceTransformer(model_name)
            await super().initialize()

    async def cleanup(self) -> None:
        """Clean up provider."""
        self._model = None
        await super().cleanup()

    def _convert_to_float_list(self, data: Any) -> list[float]:
        """Convert data to list of floats.

        Args:
            data: Data to convert.

        Returns:
            list[float]: Converted data.

        Raises:
            ProviderError: If data cannot be converted.
        """
        array = np.asarray(data, dtype=np.float64)
        if array.ndim != 1:
            raise ProviderError("Invalid data format")
        return cast(list[float], array.tolist())

    def _convert_to_float_list_list(self, data: Any) -> list[list[float]]:
        """Convert data to list of lists of floats.

        Args:
            data: Data to convert.

        Returns:
            list[list[float]]: Converted data.

        Raises:
            ProviderError: If data cannot be converted.
        """
        array = np.asarray(data, dtype=np.float64)
        if array.ndim != 2:
            raise ProviderError("Invalid data format")
        return cast(list[list[float]], array.tolist())

    async def _embed_text(self, text: str, **kwargs: Any) -> list[float]:
        """Embed text.

        Args:
            text: Text to embed.
            **kwargs: Additional arguments.

        Returns:
            list[float]: Embedding.

        Raises:
            DependencyError: If sentence-transformers is not installed.
            ProviderError: If embedding fails.
        """
        if not self._model:
            raise DependencyError(
                "Provider not initialized",
                package="sentence-transformers",
            )

        try:
            embedding = self._model.encode(text, **kwargs)
            return self._convert_to_float_list(embedding)
        except Exception as err:
            raise ProviderError("Failed to generate embedding") from err

    async def _embed_texts(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Embed texts.

        Args:
            texts: List of texts to embed.
            **kwargs: Additional arguments.

        Returns:
            list[list[float]]: List of embeddings.

        Raises:
            DependencyError: If sentence-transformers is not installed.
            ProviderError: If embedding fails.
        """
        if not self._model:
            raise DependencyError(
                "Provider not initialized",
                package="sentence-transformers",
            )

        try:
            embeddings = self._model.encode(texts, **kwargs)
            return self._convert_to_float_list_list(embeddings)
        except Exception as err:
            raise ProviderError("Failed to generate embeddings") from err
