"""OpenAI provider implementation for LLM capabilities.

This module provides an OpenAI-based implementation of the LLM provider interface,
supporting GPT-4, GPT-3.5, and text-embedding models.

Example:
    >>> from pepperpy.llm import LLMProvider
    >>> provider = LLMProvider.from_config({
    ...     "provider": "openai",
    ...     "model": "gpt-4",
    ...     "api_key": "sk-..."
    ... })
    >>> messages = [
    ...     Message(role="system", content="You are helpful."),
    ...     Message(role="user", content="What's the weather?")
    ... ]
    >>> result = await provider.generate(messages)
    >>> print(result.content)
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Union, cast

import tiktoken
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_function_message_param import (
    ChatCompletionFunctionMessageParam,
)
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

from pepperpy.llm.base import (
    GenerationChunk,
    GenerationResult,
    LLMError,
    LLMProvider,
    Message,
    MessageRole,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of the LLM provider interface.

    This provider supports:
    - GPT-4 and GPT-3.5 models
    - Chat-based interactions
    - Streaming responses
    - Text embeddings
    - Function calling
    """

    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model to use for text generation
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            config: Optional configuration dictionary
        """
        # Initialize LLM provider
        config = config or {}
        config["api_key"] = api_key
        super().__init__(
            base_url="https://api.openai.com/v1",
            config=config,
        )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._api_key = api_key
        self._sync_client: Optional[OpenAI] = None
        self._async_client: Optional[AsyncOpenAI] = None
        self._tokenizer = None

    async def initialize(self) -> None:
        """Initialize OpenAI clients."""
        await super().initialize()
        await self._initialize_clients()

    async def cleanup(self) -> None:
        """Cleanup OpenAI clients."""
        if self._sync_client:
            await self._sync_client.close()
            self._sync_client = None
        if self._async_client:
            await self._async_client.close()
            self._async_client = None
        await super().cleanup()

    async def _initialize_clients(self) -> None:
        """Initialize OpenAI clients."""
        if not self._sync_client:
            self._sync_client = OpenAI(api_key=self._api_key)
        if not self._async_client:
            self._async_client = AsyncOpenAI(api_key=self._api_key)

        # Initialize tokenizer
        try:
            self._tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self._tokenizer = tiktoken.get_encoding("cl100k_base")

    def _convert_messages(
        self, messages: Union[str, List[Message]]
    ) -> List[ChatCompletionMessageParam]:
        """Convert messages to OpenAI format.

        Args:
            messages: String prompt or list of messages

        Returns:
            List of messages in OpenAI format

        Raises:
            ValidationError: If messages are invalid
        """
        if isinstance(messages, str):
            return [
                cast(
                    ChatCompletionUserMessageParam,
                    {
                        "role": "user",
                        "content": messages,
                    },
                )
            ]

        openai_messages: List[ChatCompletionMessageParam] = []
        for msg in messages:
            if not isinstance(msg, Message):
                raise LLMError(f"Invalid message type: {type(msg)}")

            # Create base message dict
            base_dict = {
                "content": msg.content,
            }
            if hasattr(msg, "name") and msg.name:
                base_dict["name"] = msg.name

            # Convert to appropriate OpenAI message type
            if msg.role == MessageRole.SYSTEM:
                message_dict = cast(
                    ChatCompletionSystemMessageParam,
                    {
                        "role": "system",
                        **base_dict,
                    },
                )
            elif msg.role == MessageRole.USER:
                message_dict = cast(
                    ChatCompletionUserMessageParam,
                    {
                        "role": "user",
                        **base_dict,
                    },
                )
            elif msg.role == MessageRole.ASSISTANT:
                message_dict = cast(
                    ChatCompletionAssistantMessageParam,
                    {
                        "role": "assistant",
                        **base_dict,
                    },
                )
            elif msg.role == MessageRole.FUNCTION:
                message_dict = cast(
                    ChatCompletionFunctionMessageParam,
                    {
                        "role": "function",
                        **base_dict,
                    },
                )
            else:
                raise LLMError(f"Invalid message role: {msg.role}")

            openai_messages.append(message_dict)

        return openai_messages

    def _create_generation_result(
        self,
        completion: ChatCompletion,
        messages: List[ChatCompletionMessageParam],
    ) -> GenerationResult:
        """Create a GenerationResult from OpenAI completion.

        Args:
            completion: OpenAI chat completion
            messages: Original messages in OpenAI format

        Returns:
            GenerationResult with completion details
        """
        # Convert completion message content to string
        content = completion.choices[0].message.content
        if content is None:
            content = ""
        elif not isinstance(content, str):
            # Handle content parts (e.g., for vision models)
            content = (
                " ".join(
                    part.text if hasattr(part, "text") else str(part)
                    for part in content
                )
                if content
                else ""
            )

        return GenerationResult(
            content=content,
            messages=[
                Message(
                    role=msg["role"],
                    content=str(msg.get("content", "")),
                    name=msg.get("name"),
                )
                for msg in messages
            ],
            usage=completion.usage.model_dump() if completion.usage else None,
            metadata={
                "model": completion.model,
                "created": completion.created,
                "id": completion.id,
            },
        )

    async def generate(
        self, messages: Union[str, List[Message]], **kwargs: Any
    ) -> GenerationResult:
        """Generate text using OpenAI's chat completion API.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options
                - temperature: Sampling temperature (0-2)
                - max_tokens: Maximum tokens to generate
                - stop: List of stop sequences
                - presence_penalty: Presence penalty (-2 to 2)
                - frequency_penalty: Frequency penalty (-2 to 2)
                - functions: List of function definitions
                - function_call: Function call behavior
                - response_format: Response format (e.g., {"type": "json"})

        Returns:
            GenerationResult containing the response

        Raises:
            LLMError: If generation fails
        """
        if not self._async_client:
            raise RuntimeError("OpenAI client not initialized")

        try:
            openai_messages = self._convert_messages(messages)
            completion = await self._async_client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs,
            )
            return self._create_generation_result(completion, openai_messages)

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise LLMError(f"OpenAI generation failed: {e}")

    async def stream(
        self, messages: Union[str, List[Message]], **kwargs: Any
    ) -> AsyncIterator[GenerationChunk]:
        """Generate text using OpenAI's streaming chat completion API.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options
                - temperature: Sampling temperature (0-2)
                - max_tokens: Maximum tokens to generate
                - stop: List of stop sequences
                - presence_penalty: Presence penalty (-2 to 2)
                - frequency_penalty: Frequency penalty (-2 to 2)
                - functions: List of function definitions
                - function_call: Function call behavior

        Returns:
            AsyncIterator yielding GenerationChunk objects

        Raises:
            LLMError: If generation fails
        """
        if not self._async_client:
            raise RuntimeError("OpenAI client not initialized")

        try:
            openai_messages = self._convert_messages(messages)
            stream = await self._async_client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield GenerationChunk(
                        content=chunk.choices[0].delta.content,
                        finish_reason=chunk.choices[0].finish_reason,
                        metadata={
                            "model": chunk.model,
                            "created": chunk.created,
                            "id": chunk.id,
                        },
                    )

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise LLMError(f"OpenAI streaming failed: {e}")

    async def get_embeddings(
        self, texts: Union[str, List[str]], **kwargs: Any
    ) -> List[List[float]]:
        """Generate embeddings using OpenAI's embedding API.

        Args:
            texts: String or list of strings to embed
            **kwargs: Additional embedding options
                - model: Embedding model (default: text-embedding-3-small)
                - dimensions: Output dimensions (only for ada-002)
                - encoding_format: Output format (float or base64)

        Returns:
            List of embedding vectors

        Raises:
            LLMError: If embedding fails
        """
        if not self._async_client:
            raise RuntimeError("OpenAI client not initialized")

        try:
            # Handle single text
            if isinstance(texts, str):
                texts = [texts]

            # Use embedding-specific model
            model = kwargs.pop("model", "text-embedding-ada-002")

            # Generate embeddings
            response = await self._async_client.embeddings.create(
                model=model,
                input=texts,
                **kwargs,
            )

            return [data.embedding for data in response.data]

        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise LLMError(f"OpenAI embedding failed: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI provider capabilities."""
        capabilities = super().get_capabilities()
        capabilities.update({
            "embeddings": True,
            "streaming": True,
            "chat_based": True,
            "function_calling": True,
            "supported_models": [
                "gpt-4",
                "gpt-4-turbo-preview",
                "gpt-3.5-turbo",
            ],
            "max_tokens": 4096,
        })
        return capabilities
