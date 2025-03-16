"""Embedding module for PepperPy.

This module provides functionality for generating embeddings from text using
various embedding providers. Embeddings are vector representations of text that
capture semantic meaning, allowing for similarity comparisons and other
vector-based operations.

Example:
    >>> import pepperpy as pp
    >>> embeddings = await pp.llm.embed("Hello, world!")
    >>> print(len(embeddings))
    1536  # Typical embedding dimension for OpenAI's ada-002 model
"""

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from pepperpy.core.errors import NotFoundError, PepperPyError
from pepperpy.providers.base import BaseProvider, provider_registry
from pepperpy.providers.rest_base import RESTProvider
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)

#
# Core Embedding Types
#


class EmbeddingError(PepperPyError):
    """Error raised by embedding providers."""

    pass


@dataclass
class EmbeddingOptions:
    """Options for embedding generation.

    Attributes:
        model: Model to use for embedding generation
        dimensions: Number of dimensions for the embeddings
        normalize: Whether to normalize the embeddings
        additional_options: Additional provider-specific options
    """

    model: str = "default"
    dimensions: Optional[int] = None
    normalize: bool = False
    additional_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResult:
    """Result of an embedding operation.

    Attributes:
        embedding: The generated embedding vector
        usage: Token usage information
        metadata: Additional metadata about the embedding
    """

    embedding: List[float]
    usage: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


#
# Provider Base Classes
#


class EmbeddingProvider(BaseProvider, abc.ABC):
    """Base class for embedding providers.

    All embedding providers must implement this interface to ensure consistent behavior
    across different implementations.
    """

    def __init__(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the embedding provider.

        Args:
            provider_name: Optional specific name for this provider
            model_name: Name of the embedding model
            **kwargs: Provider-specific configuration
        """
        super().__init__(
            provider_type="embedding",
            provider_name=provider_name,
            model_name=model_name,
            **kwargs,
        )
        # Add embedding-specific capabilities
        self.add_capability("text_embedding")

    @abc.abstractmethod
    async def embed(
        self, text: str, options: Optional[EmbeddingOptions] = None
    ) -> EmbeddingResult:
        """Generate embeddings for the given text.

        Args:
            text: The text to generate embeddings for
            options: Optional embedding options

        Returns:
            The generated embeddings

        Raises:
            EmbeddingError: If there is an error generating the embeddings
        """
        pass

    @abc.abstractmethod
    async def embed_batch(
        self, texts: List[str], options: Optional[EmbeddingOptions] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts.

        Args:
            texts: The texts to generate embeddings for
            options: Optional embedding options

        Returns:
            The generated embeddings for each text

        Raises:
            EmbeddingError: If there is an error generating the embeddings
        """
        pass

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return self.config.copy()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {"capabilities": list(self._capabilities)}


class RESTEmbeddingProvider(RESTProvider, EmbeddingProvider):
    """Base class for REST-based embedding providers.

    This class extends both RESTProvider and EmbeddingProvider to provide
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
        super().__init__(
            provider_name=name,
            model_name=default_model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
        self.default_model = default_model

    async def embed(
        self, text: str, options: Optional[EmbeddingOptions] = None
    ) -> EmbeddingResult:
        """Generate embeddings for the given text.

        Args:
            text: Text to embed
            options: Optional embedding options

        Returns:
            EmbeddingResult with the generated embedding

        Raises:
            EmbeddingError: If embedding fails
        """
        raise NotImplementedError("Subclasses must implement embed")

    async def embed_batch(
        self, texts: List[str], options: Optional[EmbeddingOptions] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts.

        Args:
            texts: Texts to embed
            options: Optional embedding options

        Returns:
            List of EmbeddingResult objects

        Raises:
            EmbeddingError: If embedding fails
        """
        raise NotImplementedError("Subclasses must implement embed_batch")


#
# Concrete Provider Implementations
#


class OpenAIEmbeddingProvider(RESTEmbeddingProvider):
    """OpenAI embedding provider.

    This class implements the EmbeddingProvider interface for OpenAI's embedding API.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "text-embedding-ada-002",
        organization_id: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize a new OpenAI embedding provider.

        Args:
            api_key: OpenAI API key
            default_model: Default embedding model to use
            organization_id: Optional OpenAI organization ID
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(
            name="openai",
            api_key=api_key,
            default_model=default_model,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
        self.organization_id = organization_id

    def _get_default_base_url(self) -> str:
        """Get the default base URL for the OpenAI API.

        Returns:
            The default base URL
        """
        return "https://api.openai.com/v1"

    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for OpenAI API requests.

        Returns:
            The headers for API requests
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.organization_id:
            headers["OpenAI-Organization"] = self.organization_id
        return headers

    async def embed(
        self, text: str, options: Optional[EmbeddingOptions] = None
    ) -> EmbeddingResult:
        """Generate embeddings for the given text using OpenAI's API.

        Args:
            text: Text to embed
            options: Optional embedding options

        Returns:
            EmbeddingResult with the generated embedding

        Raises:
            EmbeddingError: If embedding fails
        """
        options = options or EmbeddingOptions()
        model = options.model if options.model != "default" else self.default_model

        try:
            response = await self.post(
                "/embeddings",
                json={
                    "input": text,
                    "model": model,
                    "dimensions": options.dimensions,
                    **options.additional_options,
                },
            )

            data = response.get("data", [{}])[0]
            embedding = data.get("embedding", [])
            usage = response.get("usage", {})

            return EmbeddingResult(
                embedding=embedding,
                usage=usage,
                metadata={"model": model},
            )
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise EmbeddingError(f"Failed to generate embeddings: {e}") from e

    async def embed_batch(
        self, texts: List[str], options: Optional[EmbeddingOptions] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts using OpenAI's API.

        Args:
            texts: Texts to embed
            options: Optional embedding options

        Returns:
            List of EmbeddingResult objects

        Raises:
            EmbeddingError: If embedding fails
        """
        options = options or EmbeddingOptions()
        model = options.model if options.model != "default" else self.default_model

        try:
            response = await self.post(
                "/embeddings",
                json={
                    "input": texts,
                    "model": model,
                    "dimensions": options.dimensions,
                    **options.additional_options,
                },
            )

            data = response.get("data", [])
            usage = response.get("usage", {})

            results = []
            for item in data:
                embedding = item.get("embedding", [])
                results.append(
                    EmbeddingResult(
                        embedding=embedding,
                        usage=usage,
                        metadata={"model": model, "index": item.get("index", 0)},
                    )
                )

            return results
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise EmbeddingError(f"Failed to generate batch embeddings: {e}") from e


class CohereEmbeddingProvider(RESTEmbeddingProvider):
    """Cohere embedding provider.

    This class implements the EmbeddingProvider interface for Cohere's embedding API.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "embed-english-v3.0",
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize a new Cohere embedding provider.

        Args:
            api_key: Cohere API key
            default_model: Default embedding model to use
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(
            name="cohere",
            api_key=api_key,
            default_model=default_model,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )

    def _get_default_base_url(self) -> str:
        """Get the default base URL for the Cohere API.

        Returns:
            The default base URL
        """
        return "https://api.cohere.ai/v1"

    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for Cohere API requests.

        Returns:
            The headers for API requests
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def embed(
        self, text: str, options: Optional[EmbeddingOptions] = None
    ) -> EmbeddingResult:
        """Generate embeddings for the given text using Cohere's API.

        Args:
            text: Text to embed
            options: Optional embedding options

        Returns:
            EmbeddingResult with the generated embedding

        Raises:
            EmbeddingError: If embedding fails
        """
        return (await self.embed_batch([text], options))[0]

    async def embed_batch(
        self, texts: List[str], options: Optional[EmbeddingOptions] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts using Cohere's API.

        Args:
            texts: Texts to embed
            options: Optional embedding options

        Returns:
            List of EmbeddingResult objects

        Raises:
            EmbeddingError: If embedding fails
        """
        if not texts:
            return []

        options = options or EmbeddingOptions()
        model = options.model if options.model != "default" else self.default_model

        # Cohere-specific parameters
        additional_params = {
            "truncate": "END",
            "input_type": "search_document",
        }
        additional_params.update(options.additional_options)

        try:
            response = await self.post(
                "/embed",
                json={
                    "texts": texts,
                    "model": model,
                    **additional_params,
                },
            )

            embeddings = response.get("embeddings", [])
            meta = response.get("meta", {})

            results = []
            for idx, embedding in enumerate(embeddings):
                results.append(
                    EmbeddingResult(
                        embedding=embedding,
                        usage={
                            "total_tokens": meta.get("billed_units", {}).get(
                                "tokens", 0
                            )
                        },
                        metadata={
                            "model": model,
                            "dimensions": len(embedding),
                            "index": idx,
                        },
                    )
                )

            return results
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise EmbeddingError(f"Failed to generate batch embeddings: {e}") from e


#
# Provider Registry
#

# Register provider type with global registry
provider_registry.register("embedding", EmbeddingProvider)

# Registry of available providers
_PROVIDERS: Dict[str, Type[EmbeddingProvider]] = {}
_PROVIDER_INSTANCES: Dict[str, EmbeddingProvider] = {}


def register_provider(name: str, provider_class: Type[EmbeddingProvider]) -> None:
    """Register a provider implementation.

    Args:
        name: The name of the provider to register
        provider_class: The provider class to register
    """
    _PROVIDERS[name.lower()] = provider_class


def get_provider(
    provider_name: str, create_if_missing: bool = True, **kwargs: Any
) -> EmbeddingProvider:
    """Get a provider instance.

    Args:
        provider_name: The name of the provider to get
        create_if_missing: Whether to create the provider if it doesn't exist
        **kwargs: Additional arguments to pass to the provider constructor

    Returns:
        The provider instance

    Raises:
        NotFoundError: If the specified provider is not registered
    """
    provider_name = provider_name.lower()

    # Check if we already have an instance
    if provider_name in _PROVIDER_INSTANCES:
        return _PROVIDER_INSTANCES[provider_name]

    # Create a new instance if requested
    if create_if_missing:
        if provider_name not in _PROVIDERS:
            raise NotFoundError(
                f"Provider '{provider_name}' not found. Available providers: {list(_PROVIDERS.keys())}"
            )

        provider_class = _PROVIDERS[provider_name]
        provider = provider_class(**kwargs)
        _PROVIDER_INSTANCES[provider_name] = provider
        return provider

    raise NotFoundError(f"Provider '{provider_name}' not found")


def list_providers() -> List[str]:
    """Get the names of all available providers.

    Returns:
        A list of provider names
    """
    return list(_PROVIDERS.keys())


async def embed(
    text: str,
    provider_name: str = "openai",
    options: Optional[EmbeddingOptions] = None,
    **kwargs: Any,
) -> List[float]:
    """Generate embeddings for the given text.

    Args:
        text: The text to generate embeddings for
        provider_name: The name of the provider to use
        options: Optional embedding options
        **kwargs: Additional arguments to pass to the provider

    Returns:
        The generated embeddings

    Raises:
        PepperPyError: If there is an error generating the embeddings
    """
    try:
        provider = get_provider(provider_name, **kwargs)
        result = await provider.embed(text, options)
        return result.embedding
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        if isinstance(e, PepperPyError):
            raise
        raise PepperPyError(f"Failed to generate embeddings: {e}") from e


async def embed_batch(
    texts: List[str],
    provider_name: str = "openai",
    options: Optional[EmbeddingOptions] = None,
    **kwargs: Any,
) -> List[List[float]]:
    """Generate embeddings for multiple texts.

    Args:
        texts: The texts to generate embeddings for
        provider_name: The name of the provider to use
        options: Optional embedding options
        **kwargs: Additional arguments to pass to the provider

    Returns:
        The generated embeddings for each text

    Raises:
        PepperPyError: If there is an error generating the embeddings
    """
    try:
        provider = get_provider(provider_name, **kwargs)
        results = await provider.embed_batch(texts, options)
        return [result.embedding for result in results]
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        if isinstance(e, PepperPyError):
            raise
        raise PepperPyError(f"Failed to generate batch embeddings: {e}") from e


# Register default providers
register_provider("openai", OpenAIEmbeddingProvider)
register_provider("cohere", CohereEmbeddingProvider)


__all__ = [
    # Public API
    "embed",
    "embed_batch",
    "get_provider",
    "list_providers",
    "register_provider",
    # Types
    "EmbeddingOptions",
    "EmbeddingProvider",
    "EmbeddingResult",
    "EmbeddingError",
    # Providers
    "OpenAIEmbeddingProvider",
    "CohereEmbeddingProvider",
]
