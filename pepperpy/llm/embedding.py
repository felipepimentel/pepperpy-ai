"""Embedding functionality for PepperPy.

This module provides abstractions and implementations for working with
embeddings in PepperPy. It provides a unified interface for generating
embeddings from different providers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from pepperpy.llm.core import LLMProviderBase


@dataclass
class EmbeddingOptions:
    """Options for embedding generation.

    Attributes:
        model: Model to use for embedding generation
        dimensions: Number of dimensions for the embeddings
        normalize: Whether to normalize the embeddings
    """

    model: str = "default"
    dimensions: Optional[int] = None
    normalize: bool = False
    additional_options: Dict[str, Any] = field(default_factory=dict)


class EmbeddingProvider:
    """Provider for generating embeddings.

    This class provides a unified interface for generating embeddings
    from different providers.
    """

    def __init__(self, provider: LLMProviderBase):
        """Initialize the embedding provider.

        Args:
            provider: The LLM provider to use for embedding generation
        """
        self.provider = provider

    def embed(
        self,
        text: Union[str, List[str]],
        options: Optional[EmbeddingOptions] = None,
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text.

        Args:
            text: The text to generate embeddings for
            options: Optional embedding options

        Returns:
            The generated embeddings
        """
        options = options or EmbeddingOptions()

        if isinstance(text, str):
            return self.provider.embed(
                text,
                dimensions=options.dimensions,
                **options.additional_options,
            )
        else:
            return [
                self.provider.embed(
                    t,
                    dimensions=options.dimensions,
                    **options.additional_options,
                )
                for t in text
            ]

    async def embed_async(
        self,
        text: Union[str, List[str]],
        options: Optional[EmbeddingOptions] = None,
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text asynchronously.

        Args:
            text: The text to generate embeddings for
            options: Optional embedding options

        Returns:
            The generated embeddings
        """
        options = options or EmbeddingOptions()

        if isinstance(text, str):
            return await self.provider.embed_async(
                text,
                dimensions=options.dimensions,
                **options.additional_options,
            )
        else:
            import asyncio

            tasks = [
                self.provider.embed_async(
                    t,
                    dimensions=options.dimensions,
                    **options.additional_options,
                )
                for t in text
            ]
            return await asyncio.gather(*tasks)


# Factory function to create embedding providers
def create_embedding_provider(
    provider_type: str,
    **kwargs: Any,
) -> EmbeddingProvider:
    """Create an embedding provider.

    Args:
        provider_type: The type of provider to create
        **kwargs: Provider-specific configuration

    Returns:
        The created embedding provider
    """
    from pepperpy.llm.core import create_provider

    provider = create_provider(provider_type, **kwargs)
    return EmbeddingProvider(provider)
