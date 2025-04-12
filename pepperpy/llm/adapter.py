"""
PepperPy LLM Adapter Module.

Provides adapters for different LLM services.
"""

import json
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from enum import Enum
from typing import Any

from pepperpy.core.base import PepperpyError
from pepperpy.core.config import get_provider_api_key
from pepperpy.core.context import get_current_context
from pepperpy.core.logging import get_logger
from pepperpy.core.observability import instrument, timed_operation
from pepperpy.llm.base import BaseLLMProvider
from pepperpy.llm.base import Message as BaseMessage
from pepperpy.plugin import PepperpyPlugin

logger = get_logger(__name__)


class LLMAdapterError(PepperpyError):
    """Error raised by LLM adapters."""

    pass


class MessageRole(str, Enum):
    """Message role in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class Message:
    """Message in a conversation."""

    def __init__(
        self,
        role: str | MessageRole,
        content: str,
        name: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize a message.

        Args:
            role: Message role
            content: Message content
            name: Optional name for function/tool messages
            tool_calls: Optional tool calls for assistant messages
        """
        self.role = role.value if isinstance(role, MessageRole) else role
        self.content = content
        self.name = name
        self.tool_calls = tool_calls

    def to_dict(self) -> dict[str, Any]:
        """Convert message to a dictionary.

        Returns:
            Dictionary representation of the message
        """
        result: dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }

        if self.name:
            result["name"] = self.name

        if self.tool_calls:
            result["tool_calls"] = self.tool_calls

        return result


class LLMAdapter(PepperpyPlugin, ABC):
    """Base class for LLM adapters."""

    def __init__(
        self, config: dict[str, Any] | None = None, model: str | None = None
    ) -> None:
        """Initialize the LLM adapter.

        Args:
            config: Optional configuration dictionary
            model: Optional model name (overrides config)
        """
        super().__init__()
        self.config = config or {}
        self.model = model or self.config.get("model")
        self.initialized = False

    @instrument(name="llm_initialize")
    async def initialize(self) -> None:
        """Initialize the LLM adapter."""
        if self.initialized:
            return

        # Initialize client
        await self._initialize_client()
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        # Clean up client
        await self._cleanup_client()
        self.initialized = False

    @abstractmethod
    async def _initialize_client(self) -> None:
        """Initialize the client.

        This method should be implemented by subclasses to initialize
        the specific client for the LLM service.
        """
        pass

    @abstractmethod
    async def _cleanup_client(self) -> None:
        """Clean up the client.

        This method should be implemented by subclasses to clean up
        the specific client for the LLM service.
        """
        pass

    @instrument(name="llm_generate")
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate text using the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature
            max_tokens: Optional maximum number of tokens
            stop_sequences: Optional stop sequences
            tools: Optional tools

        Returns:
            Generated text

        Raises:
            LLMAdapterError: If generation fails
        """
        messages = []

        # Add system message if provided
        if system_prompt:
            messages.append(Message(MessageRole.SYSTEM, system_prompt))

        # Add user message
        messages.append(Message(MessageRole.USER, prompt))

        # Generate completion
        response = await self.generate_with_messages(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop_sequences=stop_sequences,
            tools=tools,
        )

        return response

    @abstractmethod
    @instrument(name="llm_generate_with_messages")
    async def generate_with_messages(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate text using messages.

        Args:
            messages: List of messages
            temperature: Optional temperature
            max_tokens: Optional maximum number of tokens
            stop_sequences: Optional stop sequences
            tools: Optional tools

        Returns:
            Generated text

        Raises:
            LLMAdapterError: If generation fails
        """
        pass

    @abstractmethod
    @instrument(name="llm_generate_stream")
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text stream.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature
            max_tokens: Optional maximum number of tokens
            stop_sequences: Optional stop sequences

        Yields:
            Chunks of generated text

        Raises:
            LLMAdapterError: If generation fails
        """
        pass


class OpenAIAdapter(LLMAdapter):
    """Adapter for OpenAI API."""

    async def _initialize_client(self) -> None:
        """Initialize the OpenAI client."""
        try:
            # Import OpenAI only when needed
            from openai import AsyncOpenAI

            # Get API key from config or environment
            api_key = self.config.get("api_key")
            if not api_key:
                # Try to get from global config using the provider API key function
                api_key = get_provider_api_key("llm", "openai")

            if not api_key:
                raise LLMAdapterError("OpenAI API key not found")

            # Create client
            self.client = AsyncOpenAI(api_key=api_key)

            # Set default model if not provided
            if not self.model:
                self.model = "gpt-4"

            logger.debug(f"Initialized OpenAI adapter with model: {self.model}")

        except ImportError:
            raise LLMAdapterError(
                "OpenAI package not installed. Install with 'pip install openai'"
            )
        except Exception as e:
            raise LLMAdapterError(f"Failed to initialize OpenAI client: {e}") from e

    async def _cleanup_client(self) -> None:
        """Clean up the OpenAI client."""
        # Nothing to clean up for OpenAI
        pass

    @instrument(name="openai_generate_with_messages")
    async def generate_with_messages(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate text using OpenAI."""
        if not self.initialized:
            await self.initialize()

        try:
            # Convert messages to OpenAI format
            openai_messages = [message.to_dict() for message in messages]

            # Set parameters
            params: dict[str, Any] = {
                "model": self.model,
                "messages": openai_messages,
            }

            if temperature is not None:
                params["temperature"] = temperature

            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            if stop_sequences:
                params["stop"] = stop_sequences

            if tools:
                params["tools"] = tools

            # Record request in context if available
            context = get_current_context()
            if context:
                context.add_metadata("llm_provider", "openai")
                context.add_metadata("llm_model", self.model)

            # Make API call
            async with timed_operation("openai_api_call"):
                completion = await self.client.chat.completions.create(**params)

            # Extract and return response
            return completion.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise LLMAdapterError(f"OpenAI generation failed: {e}") from e

    @instrument(name="openai_generate_stream")
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text stream using OpenAI."""
        if not self.initialized:
            await self.initialize()

        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Set parameters
            params: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "stream": True,
            }

            if temperature is not None:
                params["temperature"] = temperature

            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            if stop_sequences:
                params["stop"] = stop_sequences

            # Record request in context if available
            context = get_current_context()
            if context:
                context.add_metadata("llm_provider", "openai")
                context.add_metadata("llm_model", self.model)
                context.add_metadata("streaming", True)

            # Make API call
            stream = await self.client.chat.completions.create(**params)

            # Yield chunks
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI stream generation failed: {e}")
            raise LLMAdapterError(f"OpenAI stream generation failed: {e}") from e


class AnthropicAdapter(LLMAdapter):
    """Adapter for Anthropic API."""

    async def _initialize_client(self) -> None:
        """Initialize the Anthropic client."""
        try:
            # Import Anthropic only when needed
            import anthropic

            # Get API key from config or environment
            api_key = self.config.get("api_key")
            if not api_key:
                # Try to get from global config using the provider API key function
                api_key = get_provider_api_key("llm", "anthropic")

            if not api_key:
                raise LLMAdapterError("Anthropic API key not found")

            # Create client
            self.client = anthropic.AsyncAnthropic(api_key=api_key)

            # Set default model if not provided
            if not self.model:
                self.model = "claude-3-opus-20240229"

            logger.debug(f"Initialized Anthropic adapter with model: {self.model}")

        except ImportError:
            raise LLMAdapterError(
                "Anthropic package not installed. Install with 'pip install anthropic'"
            )
        except Exception as e:
            raise LLMAdapterError(f"Failed to initialize Anthropic client: {e}") from e

    async def _cleanup_client(self) -> None:
        """Clean up the Anthropic client."""
        # Nothing to clean up for Anthropic
        pass

    @instrument(name="anthropic_generate_with_messages")
    async def generate_with_messages(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate text using Anthropic."""
        if not self.initialized:
            await self.initialize()

        try:
            # Convert messages to Anthropic format
            anthropic_messages = []

            for message in messages:
                if message.role == "system":
                    # Claude handles system messages differently
                    system_prompt = message.content
                    continue

                anthropic_messages.append({
                    "role": message.role,
                    "content": message.content,
                })

            # Set parameters
            params: dict[str, Any] = {
                "model": self.model,
                "messages": anthropic_messages,
            }

            # Set system prompt if available
            if "system_prompt" in locals():
                params["system"] = system_prompt

            if temperature is not None:
                params["temperature"] = temperature

            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            if stop_sequences:
                params["stop_sequences"] = stop_sequences

            # Record request in context if available
            context = get_current_context()
            if context:
                context.add_metadata("llm_provider", "anthropic")
                context.add_metadata("llm_model", self.model)

            # Make API call
            async with timed_operation("anthropic_api_call"):
                completion = await self.client.messages.create(**params)

            # Extract and return response
            return completion.content[0].text or ""

        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise LLMAdapterError(f"Anthropic generation failed: {e}") from e

    @instrument(name="anthropic_generate_stream")
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text stream using Anthropic."""
        if not self.initialized:
            await self.initialize()

        try:
            # Prepare message
            params: dict[str, Any] = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            }

            # Set system prompt if available
            if system_prompt:
                params["system"] = system_prompt

            if temperature is not None:
                params["temperature"] = temperature

            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            if stop_sequences:
                params["stop_sequences"] = stop_sequences

            # Record request in context if available
            context = get_current_context()
            if context:
                context.add_metadata("llm_provider", "anthropic")
                context.add_metadata("llm_model", self.model)
                context.add_metadata("streaming", True)

            # Make API call
            stream = await self.client.messages.create(**params)

            # Yield chunks
            async for chunk in stream:
                if chunk.type == "content_block_delta" and chunk.delta.text:
                    yield chunk.delta.text

        except Exception as e:
            logger.error(f"Anthropic stream generation failed: {e}")
            raise LLMAdapterError(f"Anthropic stream generation failed: {e}") from e


class OllamaAdapter(LLMAdapter):
    """Adapter for Ollama API."""

    async def _initialize_client(self) -> None:
        """Initialize the Ollama client."""
        try:
            # No special package needed for Ollama, just use httpx
            import httpx

            # Get base URL from config
            self.base_url = self.config.get("base_url", "http://localhost:11434")

            # Create client
            self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

            # Set default model if not provided
            if not self.model:
                self.model = "llama3"

            logger.debug(f"Initialized Ollama adapter with model: {self.model}")

        except ImportError:
            raise LLMAdapterError(
                "httpx package not installed. Install with 'pip install httpx'"
            )
        except Exception as e:
            raise LLMAdapterError(f"Failed to initialize Ollama client: {e}") from e

    async def _cleanup_client(self) -> None:
        """Clean up the Ollama client."""
        if hasattr(self, "client"):
            await self.client.aclose()

    @instrument(name="ollama_generate_with_messages")
    async def generate_with_messages(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate text using Ollama."""
        if not self.initialized:
            await self.initialize()

        try:
            # Convert messages to Ollama format
            prompt = ""
            for message in messages:
                if message.role == "system":
                    prompt += f"<system>\n{message.content}\n</system>\n\n"
                elif message.role == "user":
                    prompt += f"<user>\n{message.content}\n</user>\n\n"
                elif message.role == "assistant":
                    prompt += f"<assistant>\n{message.content}\n</assistant>\n\n"

            prompt += "<assistant>\n"

            # Set parameters
            params: dict[str, Any] = {
                "model": self.model,
                "prompt": prompt,
            }

            if temperature is not None:
                params["temperature"] = temperature

            if max_tokens is not None:
                params["num_predict"] = max_tokens

            if stop_sequences:
                params["stop"] = stop_sequences

            # Record request in context if available
            context = get_current_context()
            if context:
                context.add_metadata("llm_provider", "ollama")
                context.add_metadata("llm_model", self.model)

            # Make API call
            async with timed_operation("ollama_api_call"):
                response = await self.client.post("/api/generate", json=params)
                response.raise_for_status()
                result = response.json()

            # Extract and return response
            return result.get("response", "")

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise LLMAdapterError(f"Ollama generation failed: {e}") from e

    @instrument(name="ollama_generate_stream")
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text stream using Ollama."""
        if not self.initialized:
            await self.initialize()

        try:
            # Prepare prompt
            full_prompt = ""
            if system_prompt:
                full_prompt += f"<system>\n{system_prompt}\n</system>\n\n"
            full_prompt += f"<user>\n{prompt}\n</user>\n\n<assistant>\n"

            # Set parameters
            params: dict[str, Any] = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": True,
            }

            if temperature is not None:
                params["temperature"] = temperature

            if max_tokens is not None:
                params["num_predict"] = max_tokens

            if stop_sequences:
                params["stop"] = stop_sequences

            # Record request in context if available
            context = get_current_context()
            if context:
                context.add_metadata("llm_provider", "ollama")
                context.add_metadata("llm_model", self.model)
                context.add_metadata("streaming", True)

            # Make API call
            async with self.client.stream(
                "POST", "/api/generate", json=params
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Ollama stream generation failed: {e}")
            raise LLMAdapterError(f"Ollama stream generation failed: {e}") from e


def create_llm_adapter(
    provider: str, model: str | None = None, **config: Any
) -> LLMAdapter:
    """Create an LLM adapter.

    Args:
        provider: Provider name (openai, anthropic, ollama)
        model: Optional model name
        **config: Additional configuration

    Returns:
        LLM adapter

    Raises:
        LLMAdapterError: If provider is invalid
    """
    # Convert provider to lowercase
    provider = provider.lower()

    # Create config with model
    adapter_config = dict(config)
    if model:
        adapter_config["model"] = model

    # Create adapter based on provider
    if provider == "openai":
        return OpenAIAdapter(adapter_config, model)
    elif provider == "anthropic":
        return AnthropicAdapter(adapter_config, model)
    elif provider == "ollama":
        return OllamaAdapter(adapter_config, model)
    else:
        raise LLMAdapterError(f"Invalid LLM provider: {provider}")


class LLMProviderAdapter(BaseLLMProvider):
    """LLM provider that uses adapters."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the LLM provider.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.adapter = None

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return
        await self._initialize_resources()
        self.initialized = True

    async def _initialize_resources(self) -> None:
        """Initialize resources."""
        # Get provider and model from config
        provider = self.config.get("provider", "openai")
        model = self.config.get("model")

        # Create adapter
        self.adapter = create_llm_adapter(provider, model, **self.config)
        if not self.adapter:
            raise LLMAdapterError(f"Failed to create adapter for provider: {provider}")

        # Initialize adapter
        await self.adapter.initialize()

    async def _cleanup_resources(self) -> None:
        """Clean up resources."""
        if self.adapter:
            await self.adapter.cleanup()

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Complete a text prompt.

        Args:
            prompt: Text prompt to complete
            **kwargs: Additional provider-specific options

        Returns:
            Completion text
        """
        if not self.initialized:
            await self.initialize()

        if not self.adapter:
            raise LLMAdapterError("LLM adapter not initialized")

        # Extract common parameters
        system_prompt = kwargs.pop("system_prompt", None)
        temperature = kwargs.pop("temperature", None)
        max_tokens = kwargs.pop("max_tokens", None)
        stop_sequences = kwargs.pop("stop_sequences", None)

        return await self.adapter.generate(
            prompt,
            system_prompt,
            temperature,
            max_tokens,
            stop_sequences,
        )

    async def chat(
        self, messages: list[BaseMessage | dict[str, str]], **kwargs: Any
    ) -> str:
        """Generate a chat response.

        Args:
            messages: List of messages
            **kwargs: Additional provider-specific options

        Returns:
            Response text
        """
        if not self.initialized:
            await self.initialize()

        if not self.adapter:
            raise LLMAdapterError("LLM adapter not initialized")

        # Convert messages to adapter format
        adapter_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                adapter_messages.append(
                    Message(
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                        name=msg.get("name"),
                    )
                )
            else:
                adapter_messages.append(
                    Message(
                        role=msg.role,
                        content=msg.content,
                        name=getattr(msg, "name", None),
                    )
                )

        # Extract common parameters
        temperature = kwargs.pop("temperature", None)
        max_tokens = kwargs.pop("max_tokens", None)
        stop_sequences = kwargs.pop("stop_sequences", None)
        tools = kwargs.pop("tools", None)

        return await self.adapter.generate_with_messages(
            adapter_messages,
            temperature,
            max_tokens,
            stop_sequences,
            tools,
        )

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed
            **kwargs: Additional provider-specific options

        Returns:
            Embedding vector
        """
        # This is a placeholder implementation since the adapters don't support embeddings yet
        # In a real implementation, this would call an embedding method on the adapter
        raise NotImplementedError("Embedding not implemented in adapter interface yet")

    @instrument(name="llm_provider_generate")
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """Generate text using the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature
            max_tokens: Optional maximum number of tokens
            stop_sequences: Optional stop sequences

        Returns:
            Generated text
        """
        if not self.initialized:
            await self.initialize()

        if not self.adapter:
            raise LLMAdapterError("LLM adapter not initialized")

        return await self.adapter.generate(
            prompt,
            system_prompt,
            temperature,
            max_tokens,
            stop_sequences,
        )

    @instrument(name="llm_provider_generate_stream")
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text stream.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature
            max_tokens: Optional maximum number of tokens
            stop_sequences: Optional stop sequences

        Yields:
            Chunks of generated text
        """
        if not self.initialized:
            await self.initialize()

        if not self.adapter:
            raise LLMAdapterError("LLM adapter not initialized")

        async for chunk in self.adapter.generate_stream(
            prompt,
            system_prompt,
            temperature,
            max_tokens,
            stop_sequences,
        ):
            yield chunk
