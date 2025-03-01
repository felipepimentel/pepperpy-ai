"""Anthropic LLM provider implementation."""

from typing import Dict, List, Optional, Union

from pepperpy.llm.base import LLMError, LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs,
    ):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-3-opus-20240229)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            **kwargs: Additional parameters to pass to Anthropic

        Raises:
            ImportError: If anthropic package is not installed
            LLMError: If initialization fails
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package is required for AnthropicProvider. "
                "Install it with: pip install anthropic"
            )

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.kwargs = kwargs

        try:
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            raise LLMError(f"Failed to initialize Anthropic client: {e}")

    def generate(
        self,
        prompt: Union[str, List[Dict[str, str]]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> str:
        """Generate text using Anthropic.

        Args:
            prompt: Text prompt or list of messages
            max_tokens: Maximum tokens to generate (overrides init value)
            temperature: Sampling temperature (overrides init value)
            **kwargs: Additional parameters to pass to Anthropic

        Returns:
            str: Generated text

        Raises:
            LLMError: If generation fails
        """
        try:
            # Convert prompt to messages if needed
            if isinstance(prompt, str):
                messages = [{"role": "user", "content": prompt}]
            else:
                messages = prompt

            # Prepare parameters
            params = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                **self.kwargs,
                **kwargs,
            }

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            # Generate response
            response = self.client.messages.create(
                messages=messages,
                **params,
            )

            return response.content[0].text

        except Exception as e:
            raise LLMError(f"Failed to generate text: {e}")

    def stream(
        self,
        prompt: Union[str, List[Dict[str, str]]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> str:
        """Stream text using Anthropic.

        Args:
            prompt: Text prompt or list of messages
            max_tokens: Maximum tokens to generate (overrides init value)
            temperature: Sampling temperature (overrides init value)
            **kwargs: Additional parameters to pass to Anthropic

        Yields:
            str: Generated text chunks

        Raises:
            LLMError: If generation fails
        """
        try:
            # Convert prompt to messages if needed
            if isinstance(prompt, str):
                messages = [{"role": "user", "content": prompt}]
            else:
                messages = prompt

            # Prepare parameters
            params = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                **self.kwargs,
                **kwargs,
            }

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            # Stream response
            with self.client.messages.stream(
                messages=messages,
                **params,
            ) as stream:
                for chunk in stream:
                    if chunk.content:
                        yield chunk.content[0].text

        except Exception as e:
            raise LLMError(f"Failed to stream text: {e}")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using Anthropic's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            int: Number of tokens

        Raises:
            LLMError: If token counting fails
        """
        try:
            return self.client.count_tokens(text)
        except Exception as e:
            raise LLMError(f"Failed to count tokens: {e}")

    def get_models(self) -> List[str]:
        """Get list of available Anthropic models.

        Returns:
            List[str]: List of model names
        """
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240229",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ]
