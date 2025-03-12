"""
REST-based LLM providers for PepperPy.

This module implements LLM providers that use REST APIs, like OpenAI and Anthropic.
"""

from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.llm.providers.base import LLMProvider, Prompt, Response, StreamingResponse
from pepperpy.providers.rest_base import RESTProvider
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


class RESTLLMProvider(RESTProvider, LLMProvider):
    """Base class for REST-based LLM providers.

    This class extends both RESTProvider and LLMProvider to provide
    a foundation for LLM providers that use REST APIs.
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        default_model: str,
        base_url: Optional[str] = None,
        timeout: int = 60,  # Longer timeout for LLM requests
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize a new REST LLM provider.

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
            name=name,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
        self.default_model = default_model

    async def complete(self, prompt: Union[str, Prompt]) -> Response:
        """Generate a completion for the given prompt.

        Args:
            prompt: Text prompt or structured Prompt object

        Returns:
            Response with generated text

        Raises:
            LLMError: If completion fails
        """
        raise NotImplementedError("Subclasses must implement complete")

    async def stream_complete(
        self, prompt: Union[str, Prompt]
    ) -> AsyncIterator[StreamingResponse]:
        """Generate a streaming completion for the given prompt.

        Args:
            prompt: Text prompt or structured Prompt object

        Yields:
            StreamingResponse chunks with generated text

        Raises:
            LLMError: If streaming completion fails
        """
        raise NotImplementedError("Subclasses must implement stream_complete")

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for the given text.

        Args:
            text: Text to embed

        Returns:
            List of embedding values

        Raises:
            LLMError: If embedding fails
        """
        raise NotImplementedError("Subclasses must implement embed")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            Dict with provider capabilities
        """
        capabilities = super().get_capabilities()
        capabilities.update({
            "supports_streaming": True,
            "supports_embeddings": True,
            "default_model": self.default_model,
        })
        return capabilities


class OpenAIProvider(RESTLLMProvider):
    """OpenAI provider implementation.

    This class implements the LLM provider interface for OpenAI's API.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-3.5-turbo",
        organization_id: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize a new OpenAI provider.

        Args:
            api_key: OpenAI API key
            default_model: Default model to use
            organization_id: OpenAI organization ID
            base_url: Custom base URL (for Azure OpenAI, etc.)
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
            organization_id=organization_id,
            **kwargs,
        )
        self.organization_id = organization_id

    def _get_default_base_url(self) -> str:
        """Get the default base URL for OpenAI API."""
        return "https://api.openai.com/v1"

    def _get_headers(self) -> Dict[str, str]:
        """Get the default headers including authentication.

        Returns:
            Dict with headers
        """
        headers = super()._get_headers()
        if self.organization_id:
            headers["OpenAI-Organization"] = self.organization_id
        return headers

    async def complete(self, prompt: Union[str, Prompt]) -> Response:
        """Generate a completion using OpenAI's API.

        Args:
            prompt: Text prompt or structured Prompt object

        Returns:
            Response with generated text

        Raises:
            LLMError: If completion fails
        """
        # This is a stub implementation to satisfy the linter
        # Actual implementation would make API calls to OpenAI
        return Response(
            text="This is a stub response from OpenAI",
            model=self.default_model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            raw_response={},
        )

    async def stream_complete(
        self, prompt: Union[str, Prompt]
    ) -> AsyncIterator[StreamingResponse]:
        """Generate a streaming completion using OpenAI's API.

        Args:
            prompt: Text prompt or structured Prompt object

        Yields:
            StreamingResponse chunks with generated text

        Raises:
            LLMError: If streaming completion fails
        """

        # This is a stub implementation to satisfy the linter
        # In a real implementation, this would be a proper async generator
        async def _stream_generator():
            yield StreamingResponse(
                text="This is a stub streaming response from OpenAI",
                model=self.default_model,
                raw_response={},
                is_finished=True,
            )

        return _stream_generator()

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI's API.

        Args:
            text: Text to embed

        Returns:
            List of embedding values

        Raises:
            LLMError: If embedding fails
        """
        # This is a stub implementation to satisfy the linter
        # Actual implementation would make API calls to OpenAI
        return [0.0] * 1536  # Return a vector of zeros with typical embedding dimension


class AnthropicProvider(RESTLLMProvider):
    """Anthropic provider implementation.

    This class implements the LLM provider interface for Anthropic's API.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "claude-2",
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize a new Anthropic provider.

        Args:
            api_key: Anthropic API key
            default_model: Default model to use
            base_url: Custom base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(
            name="anthropic",
            api_key=api_key,
            default_model=default_model,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )

    def _get_default_base_url(self) -> str:
        """Get the default base URL for Anthropic API."""
        return "https://api.anthropic.com/v1"

    def _get_headers(self) -> Dict[str, str]:
        """Get the default headers including authentication.

        Returns:
            Dict with headers
        """
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "User-Agent": "PepperPy/1.0",
        }
        return headers

    async def complete(self, prompt: Union[str, Prompt]) -> Response:
        """Generate a completion using Anthropic's API.

        Args:
            prompt: Text prompt or structured Prompt object

        Returns:
            Response with generated text

        Raises:
            LLMError: If completion fails
        """
        # This is a stub implementation to satisfy the linter
        # Actual implementation would make API calls to Anthropic
        return Response(
            text="This is a stub response from Anthropic",
            model=self.default_model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            raw_response={},
        )

    async def stream_complete(
        self, prompt: Union[str, Prompt]
    ) -> AsyncIterator[StreamingResponse]:
        """Generate a streaming completion using Anthropic's API.

        Args:
            prompt: Text prompt or structured Prompt object

        Yields:
            StreamingResponse chunks with generated text

        Raises:
            LLMError: If streaming completion fails
        """

        # This is a stub implementation to satisfy the linter
        # In a real implementation, this would be a proper async generator
        async def _stream_generator():
            yield StreamingResponse(
                text="This is a stub streaming response from Anthropic",
                model=self.default_model,
                raw_response={},
                is_finished=True,
            )

        return _stream_generator()

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using Anthropic's API.

        Args:
            text: Text to embed

        Returns:
            List of embedding values

        Raises:
            LLMError: If embedding fails
        """
        # This is a stub implementation to satisfy the linter
        # Actual implementation would make API calls to Anthropic
        return [0.0] * 1024  # Return a vector of zeros with typical embedding dimension
