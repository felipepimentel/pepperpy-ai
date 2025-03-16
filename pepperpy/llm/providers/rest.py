"""
REST-based LLM providers for PepperPy.

This module implements LLM providers that use REST APIs, like OpenAI and Anthropic.
"""

from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.llm.providers.base import (
    LLMProvider,
    LLMResult,
    Message,
)
from pepperpy.providers.rest_base import RESTProvider
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


class RESTLLMProvider(RESTProvider, LLMProvider):
    """Base class for REST-based LLM providers.

    This class extends both RESTProvider and LLMProvider to provide
    a foundation for providers that use REST APIs.
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        default_model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs,
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
            provider_name=name,
            model_name=default_model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
        self.default_model = default_model

    async def generate(self, prompt: Union[str, List[Message]], **options) -> LLMResult:
        """Generate text using the provider's API.

        Args:
            prompt: The prompt to generate text from
            **options: Additional options for generation

        Returns:
            The generated text result

        Raises:
            LLMError: If generation fails
        """
        raise NotImplementedError("Subclasses must implement generate")

    async def generate_stream(
        self, prompt: Union[str, List[Message]], **options
    ) -> AsyncIterator[LLMResult]:
        """Generate text in a streaming fashion.

        Args:
            prompt: The prompt to generate text from
            **options: Additional options for generation

        Yields:
            The generated text chunks

        Raises:
            LLMError: If generation fails
        """
        raise NotImplementedError("Subclasses must implement generate_stream")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this provider.

        Returns:
            A dictionary of capabilities
        """
        capabilities = super().get_capabilities()
        capabilities.update({
            "supports_streaming": False,
            "chat_based": False,
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

    async def generate(self, prompt: Union[str, List[Message]], **options) -> LLMResult:
        """Generate text using OpenAI's API.

        Args:
            prompt: Text prompt or list of messages
            **options: Additional options for generation

        Returns:
            LLMResult with generated text

        Raises:
            LLMError: If generation fails
        """
        # This is a stub implementation to satisfy the linter
        # Actual implementation would make API calls to OpenAI
        return LLMResult(
            text="This is a stub response from OpenAI",
            model_name=self.default_model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            metadata={},
        )

    async def generate_stream(
        self, prompt: Union[str, List[Message]], **options
    ) -> AsyncIterator[LLMResult]:
        """Generate text in a streaming fashion using OpenAI's API.

        Args:
            prompt: Text prompt or list of messages
            **options: Additional options for generation

        Yields:
            LLMResult chunks with generated text

        Raises:
            LLMError: If generation fails
        """

        # This is a stub implementation to satisfy the linter
        # In a real implementation, this would be a proper async generator
        async def _stream_generator():
            yield LLMResult(
                text="This is a stub streaming response from OpenAI",
                model_name=self.default_model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata={"is_finished": True},
            )

        return _stream_generator()


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
        headers = super()._get_headers()
        headers["anthropic-version"] = "2023-06-01"
        return headers

    async def generate(self, prompt: Union[str, List[Message]], **options) -> LLMResult:
        """Generate text using Anthropic's API.

        Args:
            prompt: Text prompt or list of messages
            **options: Additional options for generation

        Returns:
            LLMResult with generated text

        Raises:
            LLMError: If generation fails
        """
        # This is a stub implementation to satisfy the linter
        # Actual implementation would make API calls to Anthropic
        return LLMResult(
            text="This is a stub response from Anthropic",
            model_name=self.default_model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            metadata={},
        )

    async def generate_stream(
        self, prompt: Union[str, List[Message]], **options
    ) -> AsyncIterator[LLMResult]:
        """Generate text in a streaming fashion using Anthropic's API.

        Args:
            prompt: Text prompt or list of messages
            **options: Additional options for generation

        Yields:
            LLMResult chunks with generated text

        Raises:
            LLMError: If generation fails
        """

        # This is a stub implementation to satisfy the linter
        # In a real implementation, this would be a proper async generator
        async def _stream_generator():
            yield LLMResult(
                text="This is a stub streaming response from Anthropic",
                model_name=self.default_model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata={"is_finished": True},
            )

        return _stream_generator()
