"""Anthropic provider implementation.

This module provides an implementation of the Anthropic provider for the PepperPy LLM module.
"""

import json
from typing import Any, AsyncIterator, Dict, Optional, Union

import httpx

from pepperpy.llm.errors import (
    LLMConfigError,
    LLMError,
)
from pepperpy.llm.providers.anthropic.config import AnthropicConfig, get_config
from pepperpy.llm.providers.anthropic.utils import (
    convert_prompt_to_anthropic_params,
    handle_anthropic_error,
)
from pepperpy.llm.providers.base import LLMProvider, Response, StreamingResponse
from pepperpy.llm.utils import Prompt, retry, validate_prompt, with_timeout
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic provider implementation.

    This provider integrates with Anthropic's API to provide access to models
    like Claude and its variants.
    """

    def __init__(self, config: Optional[AnthropicConfig] = None):
        """Initialize the Anthropic provider.

        Args:
            config: The provider configuration, or None to use the default
        """
        self.config = config or get_config()

        if not self.config.api_key:
            raise LLMConfigError(
                "Anthropic API key is required",
                provider="anthropic",
            )

        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )

    async def close(self) -> None:
        """Close the provider and release resources."""
        await self.client.aclose()

    @retry(max_retries=3)
    async def complete(self, prompt: Union[str, Prompt]) -> Response:
        """Generate a completion for the given prompt.

        Args:
            prompt: The prompt to generate a completion for

        Returns:
            The generated completion

        Raises:
            LLMError: If there is an error generating the completion
        """
        # Validate and normalize the prompt
        prompt_obj = validate_prompt(prompt)

        # Convert the prompt to Anthropic parameters
        params = convert_prompt_to_anthropic_params(prompt_obj)

        # Add the model parameter
        params["model"] = self.config.default_model

        try:
            # Make the API request
            response = await with_timeout(
                self.client.post,
                self.config.timeout,
                "/v1/messages",
                json=params,
            )

            # Check for errors
            response.raise_for_status()

            # Parse the response
            data = response.json()

            # Extract the completion
            content = data.get("content", [])
            if not content:
                raise LLMError(
                    "No completion content returned",
                    provider="anthropic",
                )

            # Get the text from the content blocks
            text = ""
            for block in content:
                if block.get("type") == "text":
                    text += block.get("text", "")

            # Create the response
            return Response(
                text=text,
                usage=data.get("usage", {}),
                metadata={
                    "model": data.get("model"),
                    "id": data.get("id"),
                    "type": data.get("type"),
                    "stop_reason": data.get("stop_reason"),
                    "stop_sequence": data.get("stop_sequence"),
                },
            )
        except httpx.HTTPStatusError as e:
            handle_anthropic_error(e)
            # This line is needed to satisfy the type checker, but it will never be reached
            # because handle_anthropic_error always raises an exception
            raise LLMError("Unexpected error", provider="anthropic")
        except httpx.RequestError as e:
            raise LLMError(
                f"Error making request to Anthropic API: {e}",
                provider="anthropic",
            )
        except Exception as e:
            raise LLMError(
                f"Unexpected error with Anthropic API: {e}",
                provider="anthropic",
            )

    @retry(max_retries=3)
    async def stream_complete(
        self, prompt: Union[str, Prompt]
    ) -> AsyncIterator[StreamingResponse]:
        """Generate a streaming completion for the given prompt.

        Args:
            prompt: The prompt to generate a completion for

        Returns:
            An async iterator of response chunks

        Raises:
            LLMError: If there is an error generating the completion
        """
        # Validate and normalize the prompt
        prompt_obj = validate_prompt(prompt)

        # Convert the prompt to Anthropic parameters
        params = convert_prompt_to_anthropic_params(prompt_obj)

        # Add the model and stream parameters
        params["model"] = self.config.default_model
        params["stream"] = True

        try:
            # Make the API request
            async with self.client.stream(
                "POST",
                "/v1/messages",
                json=params,
                timeout=self.config.timeout,
            ) as response:
                # Check for errors
                response.raise_for_status()

                # Process the streaming response
                async for line in response.aiter_lines():
                    # Skip empty lines
                    line = line.strip()
                    if not line:
                        continue

                    # Skip the "data: " prefix
                    if line.startswith("data: "):
                        line = line[6:]

                    # Skip the "[DONE]" message
                    if line == "[DONE]":
                        break

                    try:
                        # Parse the JSON data
                        data = json.loads(line)

                        # Extract the delta
                        delta = data.get("delta", {})
                        if not delta:
                            continue

                        # Get the text from the delta
                        text = delta.get("text", "")

                        # Skip empty content
                        if not text:
                            continue

                        # Check if this is the last chunk
                        is_finished = data.get("type") == "message_stop"

                        # Yield the streaming response
                        yield StreamingResponse(
                            text=text,
                            is_finished=is_finished,
                            metadata={
                                "model": data.get("model"),
                                "id": data.get("id"),
                                "type": data.get("type"),
                                "stop_reason": data.get("stop_reason"),
                                "stop_sequence": data.get("stop_sequence"),
                            },
                        )
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse streaming response: {line}")
                        continue
        except httpx.HTTPStatusError as e:
            handle_anthropic_error(e)
            # This line will never be reached as handle_anthropic_error always
            # raises an exception, but we include it to satisfy the type checker
            raise LLMError(f"Error handling HTTP status: {e}", provider="anthropic")
        except httpx.RequestError as e:
            raise LLMError(
                f"Error making request to Anthropic API: {e}",
                provider="anthropic",
            )
        except Exception as e:
            raise LLMError(
                f"Unexpected error with Anthropic API: {e}",
                provider="anthropic",
            )

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return {
            "provider": "anthropic",
            "default_model": self.config.default_model,
            "models": {
                name: {
                    "name": model.name,
                    "max_tokens": model.max_tokens,
                    "supports_vision": model.supports_vision,
                }
                for name, model in self.config.models.items()
            },
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            The provider capabilities
        """
        return {
            "provider": "anthropic",
            "supports_streaming": True,
            "chat_based": True,
            "default_model": self.config.default_model,
        }
