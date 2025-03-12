"""
REST-based RAG providers for PepperPy.

This module implements RAG providers that use REST APIs for embedding,
reranking, and generation.
"""

from typing import Any, Dict, List, Optional

from pepperpy.providers.rest_base import RESTProvider
from pepperpy.rag.providers.base import (
    BaseEmbeddingProvider,
    BaseGenerationProvider,
    BaseRerankingProvider,
)
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


class RESTEmbeddingProvider(RESTProvider, BaseEmbeddingProvider):
    """Base class for REST-based embedding providers.

    This class extends both RESTProvider and BaseEmbeddingProvider to provide
    a foundation for embedding providers that use REST APIs.
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        default_model: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize a new REST embedding provider.

        Args:
            name: Provider name
            api_key: Authentication key
            default_model: Default model to use
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional provider-specific configuration
        """
        RESTProvider.__init__(
            self,
            name=name,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
        BaseEmbeddingProvider.__init__(self, model_name=default_model)
        self.default_model = default_model

    async def _embed_texts(
        self,
        texts: List[str],
        **kwargs: Any,
    ) -> List[List[float]]:
        """Generate embeddings for the given texts.

        Args:
            texts: List of texts to embed
            **kwargs: Additional embedding parameters

        Returns:
            List of embedding vectors

        Raises:
            ProviderError: If embedding fails
        """
        raise NotImplementedError("Subclasses must implement _embed_texts")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            Dict with provider capabilities
        """
        capabilities = RESTProvider.get_capabilities(self)
        capabilities.update({
            "supports_embeddings": True,
            "default_model": self.default_model,
        })
        return capabilities


class RESTRerankingProvider(RESTProvider, BaseRerankingProvider):
    """Base class for REST-based reranking providers.

    This class extends both RESTProvider and BaseRerankingProvider to provide
    a foundation for reranking providers that use REST APIs.
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        default_model: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize a new REST reranking provider.

        Args:
            name: Provider name
            api_key: Authentication key
            default_model: Default model to use
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional provider-specific configuration
        """
        RESTProvider.__init__(
            self,
            name=name,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
        BaseRerankingProvider.__init__(self, model_name=default_model)
        self.default_model = default_model

    async def _compute_scores(
        self,
        query: str,
        documents: List[str],
        scores: Optional[List[float]] = None,
    ) -> List[float]:
        """Compute relevance scores for documents.

        Args:
            query: Query to compute scores for
            documents: List of documents to score
            scores: Optional initial scores

        Returns:
            List of relevance scores

        Raises:
            ProviderError: If scoring fails
        """
        raise NotImplementedError("Subclasses must implement _compute_scores")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            Dict with provider capabilities
        """
        capabilities = RESTProvider.get_capabilities(self)
        capabilities.update({
            "supports_reranking": True,
            "default_model": self.default_model,
        })
        return capabilities


class RESTGenerationProvider(RESTProvider, BaseGenerationProvider):
    """Base class for REST-based generation providers.

    This class extends both RESTProvider and BaseGenerationProvider to provide
    a foundation for generation providers that use REST APIs.
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        default_model: str,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        default_prompt_template: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a new REST generation provider.

        Args:
            name: Provider name
            api_key: Authentication key
            default_model: Default model to use
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            default_prompt_template: Default prompt template
            **kwargs: Additional provider-specific configuration
        """
        RESTProvider.__init__(
            self,
            name=name,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
        BaseGenerationProvider.__init__(
            self,
            model_name=default_model,
            default_prompt_template=default_prompt_template,
        )
        self.default_model = default_model

    async def _generate_text(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Generate text based on the prompt.

        Args:
            prompt: Prompt to generate text from
            **kwargs: Additional generation parameters

        Returns:
            Generated text

        Raises:
            ProviderError: If generation fails
        """
        raise NotImplementedError("Subclasses must implement _generate_text")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            Dict with provider capabilities
        """
        capabilities = RESTProvider.get_capabilities(self)
        capabilities.update({
            "supports_generation": True,
            "default_model": self.default_model,
        })
        return capabilities
