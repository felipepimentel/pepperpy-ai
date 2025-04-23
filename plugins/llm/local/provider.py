"""
Local LLM provider for running models on your own hardware

This provider implements a llm plugin for the PepperPy framework.
"""

import os
from collections.abc import AsyncIterator
import collections.abc
from typing import dict, list, set, Any

from pepperpy.core.errors import PepperpyError
from pepperpy.llm.base import LLMProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.llm.base import LlmError
from pepperpy.llm.base import LlmError

logger = logger.getLogger(__name__)


class LLMError(class LLMError(PepperpyError):
    """Error raised by LLM providers."""):
    """
    Llm llmerror provider.
    
    This provider implements llmerror functionality for the PepperPy llm framework.
    """

    pass


class GenerationResult:
    """Result of a text generation."""

    def __init__(self, content: str, **kwargs: Any):
        """Initialize the result.

        Args:
            content: Generated content
            **kwargs: Additional metadata
        """
        self.content = content
        self.metadata = kwargs

    def __str__(self) -> str:


    """Return the content as string.



    Returns:


        Return description


    """
        return self.content


class GenerationChunk:
    """Chunk of a streaming generation result."""

    def __init__(self, content: str, **kwargs: Any):
        """Initialize the chunk.

        Args:
            content: Chunk content
            **kwargs: Additional metadata
        """
        self.content = content
        self.metadata = kwargs

    def __str__(self) -> str:


    """Return the content as string.



    Returns:


        Return description


    """
        return self.content


class LocalProvider(LLMProvider, BasePluginProvider):
    """
    Local LLM provider for running models on your own hardware

    This provider implements interfaces with locally running models (llama.cpp, oobabooga, etc.).
    """

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
 """
        # Skip if already initialized
        if self.initialized:
            return

        # Call the base class implementation first
        await super().initialize()

        # Initialize local model client
        try:
            # Get configuration parameters
            model_path = self.model_path
            host = self.host
            port = self.port
            api_type = self.api_type.lower()

            if not model_path and not (host and port):
                self.logger.warning(
                    "No model path or host:port specified, will use mock responses"
                )
                self.client = None
                return

            # Import client library based on api_type
            if api_type == "llama.cpp":
                try:
                    # Try to import llama.cpp Python bindings
                    import llama_cpp

                    self.client = llama_cpp.Llama(
                        model_path=model_path,
                        n_ctx=self.context_length,
                        n_threads=self.threads or 4),
                    )
                except ImportError:
                    self.logger.warning(
                        "llama_cpp package not installed, trying HTTP API"
                    )
                    await self._setup_http_client(host, port)
            elif api_type == "oobabooga":
                await self._setup_http_client(host, port, api_type="oobabooga")
            else:
                # Default to HTTP client
                await self._setup_http_client(host, port)

            self.logger.debug(f"Initialized local LLM with api_type={api_type}")

        except Exception as e:
            raise LLMError(f"Failed to initialize local model client: {e}") from e

    async def _setup_http_client(
        self, host: str, port: int, api_type: str = "default"
    ) -> None:
        """set up HTTP client for remote local models.

        Args:
            host: API host
            port: API port
            api_type: Type of API (default, oobabooga, etc.)
        """
        try:
            import aiohttp

            self.client = aiohttp.ClientSession()
            self.api_base_url = f"http://{host}:{port}"
            self.api_type = api_type
        except ImportError:
            self.logger.warning(
                "aiohttp package not installed. Will use mock responses."
            )
            self.client = None

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
 """
        # Clean up client if it exists
        if hasattr(self, "client") and self.client:
            # Close aiohttp session if it's that type
            if hasattr(self.client, "close") and callable(self.client.close):
                await self.client.close()

            self.client = None

        # Call the base class cleanup
        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task based on input data.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result
        """
        # Get task type from input
        task_type = input_data.get("task")

        if not task_type:
            raise LlmError("No task specified")

        try:
            # Ensure initialization
            if not self.initialized:
                await self.initialize()

            # Handle different task types
            if task_type == "chat":
                messages = input_data.get("messages", [])
                response = await self.generate(
                    messages, **input_data.get("options", {})
                )
                return {"status": "success", "result": response.content}
            elif task_type == "completion":
                prompt = input_data.get("prompt", "")
                if not prompt:
                    raise LlmError("No prompt provided")

                # Convert prompt to message format
                messages = [{"role": "user", "content": prompt}]
                response = await self.generate(
                    messages, **input_data.get("options", {})
                )
                return {"status": "success", "result": response.content}
            elif task_type == "stream":
                messages = input_data.get("messages", [])
                # For API responses, this will actually stream
                # But we need to return something directly here
                generation = self.stream(messages, **input_data.get("options", {}))
                response = await self.generate(
                    messages, **input_data.get("options", {})
                )
                return {"status": "success", "result": response.content}
            else:
                raise LlmError(f"Unknown task type: {task_type)"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "message": str(e)}

    def _convert_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Convert PepperPy messages to a standard format.

        Args:
            messages: list of messages to convert

        Returns:
            list of properly formatted messages
        """
        formatted_messages = []

        for msg in messages:
            if isinstance(msg, dict):
                # Already in dict format, ensure it has role and content
                if "role" not in msg or "content" not in msg:
                    raise LLMError(f"Invalid message format: {msg}")
                formatted_messages.append(msg)
            elif hasattr(msg, "role") and hasattr(msg, "content"):
                # Convert Message-like object to dict
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                raise LLMError(f"Unsupported message type: {type(msg).__name__}")

        return formatted_messages

    def _format_prompt(self, messages: list[dict[str, Any]]) -> str:
        """Format messages as a prompt string for text completion models.

        Args:
            messages: list of message dictionaries

        Returns:
            Formatted prompt string
        """
        prompt = ""
        for msg in messages:
            role = msg["role"].lower()
            content = msg["content"]

            if role == "system":
                prompt += f"### System:\n{content}\n\n"
            elif role == "user":
                prompt += f"### User:\n{content}\n\n"
            elif role == "assistant":
                prompt += f"### Assistant:\n{content}\n\n"
            else:
                prompt += f"### {role.capitalize()}:\n{content}\n\n"

        prompt += "### Assistant:\n"
        return prompt

    async def generate(self, messages: list[Any], **kwargs: Any) -> GenerationResult:
        """Generate a response using the LLM.

        Args:
            messages: list of messages to generate a response for
            **kwargs: Additional parameters for the generation

        Returns:
            Generated response
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Convert messages to standard format
            formatted_messages = self._convert_messages(messages)

            # Get parameters with defaults from config
            model = kwargs.get("model", self.model)
            temperature = kwargs.get("temperature", self.temperature)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)

            # If client exists, call local model API
            if self.client:
                # Handle different client types
                if hasattr(self.client, "close") and callable(self.client.close):
                    # This is an HTTP client (aiohttp session)
                    return await self._generate_via_http(
                        formatted_messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs,
                    )
                elif hasattr(self.client, "create_completion"):
                    # This is a local llama_cpp client
                    prompt = self._format_prompt(formatted_messages)
                    completion = self.client.create_completion(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stop=kwargs.get("stop", ["### User:", "\n\n"]),
                    )
                    return GenerationResult(
                        content=completion["choices"][0]["text"].strip(),
                        model=model,
                    )
                else:
                    # Unknown client type, use mock
                    return self._mock_response(model)
            else:
                # No client, use mock
                return self._mock_response(model)

        except Exception as e:
            raise LLMError(f"Error generating response: {e}") from e

    async def _generate_via_http(
        self,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate response using HTTP API.

        Args:
            messages: list of formatted message dictionaries
            model: Model name/path
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        if (
            not hasattr(self, "api_type")
            or not hasattr(self, "api_base_url")
            or not self.client
        ):
            return self._mock_response(model)

        try:
            # Different payload formats for different APIs
            if self.api_type == "oobabooga":
                # Oobabooga API format
                prompt = self._format_prompt(messages)
                payload = {
                    "prompt": prompt,
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "stop": kwargs.get("stop", ["### User:", "\n\n"]),
                    "do_sample": True,
                }
                endpoint = f"{self.api_base_url}/api/v1/generate"
            else:
                # Default to OpenAI-compatible API format
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                endpoint = f"{self.api_base_url}/v1/chat/completions"

            # Send request
            async with self.client.post(endpoint, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMError(f"API error ({response.status}): {error_text}")

                result = await response.json()

                # Extract content based on API type
                if self.api_type == "oobabooga":
                    content = result.get("results", [{"text": ""}])[0]["text"]
                else:
                    # OpenAI-compatible format
                    content = (
                        result.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )

                return GenerationResult(
                    content=content, model=model, raw_response=result
                )

        except Exception as e:
            self.logger.error(f"Error in HTTP request: {e}")
            return self._mock_response(model)

    def _mock_response(self, model: str) -> GenerationResult:
        """Create a mock response for testing without a local model.

        Args:
            model: Model name

        Returns:
            Mock response
        """
        self.logger.warning(f"Using mock response for model {model}")
        return GenerationResult(
            content=f"This is a mock response from the Local LLM provider using {model}.",
            model=model,
        )

    async def stream(
        self, messages: list[Any], **kwargs: Any
    ) -> AsyncIterator[GenerationChunk]:
        """Stream a response using the LLM.

        Args:
            messages: list of messages to generate a response for
            **kwargs: Additional parameters for the generation

        Returns:
            Iterator of response chunks
        """
        if not self.initialized:
            await self.initialize()

        try:
            # If no client or it's not an HTTP client, use mock streaming
            if not self.client or not (
                hasattr(self.client, "close") and callable(self.client.close)
            ):
                yield GenerationChunk(content="This is a mock ")
                yield GenerationChunk(content="streaming response ")
                yield GenerationChunk(content="from the Local provider.")
                return

            # Convert messages to standard format
            formatted_messages = self._convert_messages(messages)

            # Get parameters with defaults from config
            model = kwargs.get("model", self.model)
            temperature = kwargs.get("temperature", self.temperature)
            max_tokens = kwargs.get("max_tokens", self.max_tokens)

            # Different streaming implementations depending on API type
            if hasattr(self, "api_type") and hasattr(self, "api_base_url"):
                if self.api_type == "oobabooga":
                    # Oobabooga streaming format
                    prompt = self._format_prompt(formatted_messages)
                    async for chunk in self._stream_oobabooga(
                        prompt, temperature=temperature, max_tokens=max_tokens, **kwargs
                    ):
                        yield chunk
                else:
                    # OpenAI-compatible API
                    payload = {
                        "model": model,
                        "messages": formatted_messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": True,
                    }
                    endpoint = f"{self.api_base_url}/v1/chat/completions"

                    # Use streaming implementation
                    async for chunk in self._stream_openai_compatible(
                        endpoint, payload
                    ):
                        yield chunk
            else:
                # Fall back to mock if no API configured
                yield GenerationChunk(content="This is a mock ")
                yield GenerationChunk(content="streaming response ")
                yield GenerationChunk(content="from the Local provider.")

        except Exception as e:
            raise LLMError(f"Error streaming response: {e}") from e

    async def _stream_oobabooga(
        self, prompt: str, temperature: float, max_tokens: int, **kwargs: Any
    ) -> AsyncIterator[GenerationChunk]:
        """Stream from Oobabooga API.

        Args:
            prompt: The prompt string
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Chunks of the generated response
        """
        # Skip if client is None
        if not self.client:
            yield GenerationChunk(content="Mock response - client not available")
            return

        payload = {
            "prompt": prompt,
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "stop": kwargs.get("stop", ["### User:", "\n\n"]),
            "do_sample": True,
            "stream": True,
        }
        endpoint = f"{self.api_base_url}/api/v1/generate"

        try:
            async with self.client.post(endpoint, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMError(f"API error ({response.status}): {error_text}")

                buffer = ""
                async for line in response.content.iter_any():
                    if line:
                        line_data = line.decode("utf-8")
                        if "data: " in line_data:
                            chunk_data = line_data.replace("data: ", "")
                            try:
                                import json

                                chunk_obj = json.loads(chunk_data)
                                token = chunk_obj.get("token", {}).get("text", "")
                                if token:
                                    yield GenerationChunk(content=token)
                            except Exception:
                                # If JSON parsing fails, just yield the whole chunk
                                yield GenerationChunk(content=chunk_data)
        except Exception as e:
            self.logger.error(f"Error in streaming request: {e}")
            yield GenerationChunk(content="[Error during streaming]")

    async def _stream_openai_compatible(
        self, endpoint: str, payload: dict[str, Any]
    ) -> AsyncIterator[GenerationChunk]:
        """Stream from OpenAI-compatible API.

        Args:
            endpoint: API endpoint
            payload: Request payload

        Yields:
            Chunks of the generated response
        """
        # Skip if client is None
        if not self.client:
            yield GenerationChunk(content="Mock response - client not available")
            return

        try:
            async with self.client.post(endpoint, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMError(f"API error ({response.status}): {error_text}")

                async for line in response.content.iter_lines():
                    if line and line.strip() and line.strip() != b"data: [DONE]":
                        try:
                            import json

                            line_text = line.decode("utf-8")
                            if line_text.startswith("data: "):
                                data = json.loads(line_text[6:])
                                content = (
                                    data.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if content:
                                    yield GenerationChunk(content=content)
                        except Exception as e:
                            raise LlmError(f"Operation failed: {e}") from e
                            self.logger.error(f"Error parsing stream data: {e}")
        except Exception as e:
            raise LlmError(f"Operation failed: {e}") from e
            self.logger.error(f"Error in streaming request: {e}")
            yield GenerationChunk(content="[Error during streaming]")
