"""Cohere embedding provider.

This module provides an implementation of the EmbeddingProvider interface for Cohere's embedding API.
"""

from typing import Any, Dict, List, Optional

from ...core.http import HTTPClient
from ..base import EmbeddingError, EmbeddingOptions, EmbeddingProvider, EmbeddingResult


class CohereEmbeddingProvider(EmbeddingProvider):
    """Cohere embedding provider.

    This class implements the EmbeddingProvider interface for Cohere's embedding API.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "embed-english-v3.0",
        provider_name: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize a new Cohere embedding provider.

        Args:
            api_key: Cohere API key
            default_model: Default embedding model to use
            provider_name: Optional specific name for this provider
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional provider-specific configuration
        """
        self.name = provider_name or "cohere"
        self.api_key = api_key
        self.default_model = default_model
        self._config = {
            "default_model": default_model,
            "timeout": timeout,
            "max_retries": max_retries,
            **kwargs,
        }
        self._client = HTTPClient(base_url or "https://api.cohere.ai/v1")

    async def initialize(self) -> None:
        """Initialize the provider.

        This method starts the HTTP client session.
        """
        await self._client.start()

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
            response = await self._client.post(
                "/embed",
                data={
                    "texts": texts,
                    "model": model,
                    **additional_params,
                },
                headers=self._get_headers(),
            )

            data = response.json()
            embeddings = data.get("embeddings", [])
            meta = data.get("meta", {})

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
            raise EmbeddingError(f"Failed to generate batch embeddings: {e}") from e

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return self._config.copy()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {
            "capabilities": ["text_embedding"],
            "models": [self.default_model],
        }
