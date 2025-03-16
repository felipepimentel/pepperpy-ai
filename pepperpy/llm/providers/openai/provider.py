"""OpenAI provider implementation.

This module provides an implementation of the OpenAI provider for the PepperPy LLM module.
"""

import json
from typing import Any, AsyncIterator, Dict, Optional, Union

import httpx

from pepperpy.llm.errors import (
    LLMConfigError,
    LLMError,
)
from pepperpy.llm.providers.base import LLMProvider, Response, StreamingResponse
from pepperpy.llm.providers.openai.config import OpenAIConfig, get_config
from pepperpy.llm.providers.openai.utils import (
    convert_prompt_to_openai_params,
    handle_openai_error,
)
from pepperpy.llm.utils import Prompt, retry, validate_prompt, with_timeout
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation.

    This provider integrates with OpenAI's API to provide access to models
    like GPT-3.5, GPT-4, and their variants.
    """

    def __init__(self, config: Optional[OpenAIConfig] = None):
        """Initialize the OpenAI provider.

        Args:
            config: The provider configuration, or None to use the default
        """
        self.config = config or get_config()

        if not self.config.api_key:
            raise LLMConfigError(
                "OpenAI API key is required",
                provider="openai",
            )

        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )

        if self.config.organization_id:
            self.client.headers["OpenAI-Organization"] = self.config.organization_id

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

        # Convert the prompt to OpenAI parameters
        params = convert_prompt_to_openai_params(prompt_obj)

        # Add the model parameter
        params["model"] = self.config.default_model

        try:
            # Make the API request
            response = await with_timeout(
                self.client.post,
                self.config.timeout,
                "/chat/completions",
                json=params,
            )

            # Check for errors
            response.raise_for_status()

            # Parse the response
            data = response.json()

            # Extract the completion
            choices = data.get("choices", [])
            if not choices:
                raise LLMError(
                    "No completion choices returned",
                    provider="openai",
                )

            # Get the first choice
            choice = choices[0]
            message = choice.get("message", {})
            content = message.get("content", "")

            # Create the response
            return Response(
                text=content,
                usage=data.get("usage", {}),
                metadata={
                    "model": data.get("model"),
                    "id": data.get("id"),
                    "created": data.get("created"),
                    "finish_reason": choice.get("finish_reason"),
                },
            )
        except httpx.HTTPStatusError as e:
            # Handle OpenAI-specific errors
            handle_openai_error(e)
            # This line will never be reached as handle_openai_error always raises an exception,
            # but we include it to satisfy the type checker
            raise LLMError(f"Error handling HTTP status: {e}", provider="openai")
        except httpx.RequestError as e:
            raise LLMError(
                f"Error making request to OpenAI API: {e}",
                provider="openai",
            )
        except Exception as e:
            raise LLMError(
                f"Unexpected error with OpenAI API: {e}",
                provider="openai",
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

        # Convert the prompt to OpenAI parameters
        params = convert_prompt_to_openai_params(prompt_obj)

        # Add the model and stream parameters
        params["model"] = self.config.default_model
        params["stream"] = True

        try:
            # Make the API request
            async with self.client.stream(
                "POST",
                "/chat/completions",
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

                        # Extract the completion
                        choices = data.get("choices", [])
                        if not choices:
                            continue

                        # Get the first choice
                        choice = choices[0]
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")

                        # Skip empty content
                        if not content:
                            continue

                        # Check if this is the last chunk
                        is_finished = choice.get("finish_reason") is not None

                        # Yield the streaming response
                        yield StreamingResponse(
                            text=content,
                            is_finished=is_finished,
                            metadata={
                                "model": data.get("model"),
                                "id": data.get("id"),
                                "created": data.get("created"),
                                "finish_reason": choice.get("finish_reason"),
                            },
                        )
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse streaming response: {line}")
                        continue
        except httpx.HTTPStatusError as e:
            handle_openai_error(e)
        except httpx.RequestError as e:
            raise LLMError(
                f"Error making request to OpenAI API: {e}",
                provider="openai",
            )
        except Exception as e:
            raise LLMError(
                f"Unexpected error with OpenAI API: {e}",
                provider="openai",
            )

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return {
            "provider": "openai",
            "default_model": self.config.default_model,
            "models": {
                name: {
                    "name": model.name,
                    "max_tokens": model.max_tokens,
                    "supports_functions": model.supports_functions,
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
            "provider": "openai",
            "supports_streaming": True,
            "chat_based": True,
            "default_model": self.config.default_model,
        }
