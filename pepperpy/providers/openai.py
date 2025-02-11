"""OpenAI provider implementation.

This module provides an implementation of the BaseProvider for OpenAI's API.
Also supports OpenRouter API which is compatible with OpenAI's API format.
"""

import os
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, Dict, List, Optional, Union, cast
from uuid import uuid4

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from pepperpy.core.types import (
    Message,
    MessageType,
    Response,
    ResponseStatus,
)
from pepperpy.monitoring import bind_logger
from pepperpy.providers.base import BaseProvider, ProviderConfig
from pepperpy.providers.domain import ProviderAPIError, ProviderError

# Configure logger
logger = bind_logger(provider="openai")

# OpenRouter base URL
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation."""

    def __init__(self, config: Optional[ProviderConfig] = None):
        """Initialize the OpenAI provider.

        Args:
        ----
            config: Provider configuration

        """
        super().__init__(config or ProviderConfig())
        self.client: Optional[AsyncOpenAI] = None

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        try:
            api_key = (
                self.config.api_key.get_secret_value()
                if self.config.api_key
                else os.getenv("OPENAI_API_KEY")
            )
            if not api_key:
                raise ProviderError("OpenAI API key not found")

            # Support for OpenRouter
            base_url = None
            if self.config.provider_type == "openrouter":
                base_url = OPENROUTER_BASE_URL
                api_key = os.getenv("PEPPERPY_API_KEY", api_key)

            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
            self._logger.info(
                "Client initialized",
                provider=self.config.provider_type,
                model=self.config.model,
            )
            self._initialized = True
        except Exception as e:
            self._logger.error(
                "Failed to initialize client",
                error=str(e),
                provider=self.config.provider_type,
            )
            raise ProviderError(str(e)) from e

    async def cleanup(self) -> None:
        """Clean up the OpenAI client."""
        if self.client:
            await self.client.close()
            self.client = None
            self._initialized = False

    async def generate(self, messages: List[Message], **kwargs: Any) -> Response:
        """Generate a response using OpenAI's API.

        Args:
        ----
            messages: List of messages to generate from
            **kwargs: Additional generation parameters

        Returns:
        -------
            The generated response

        Raises:
        ------
            ProviderError: If generation fails

        """
        self._check_initialized()

        try:
            if not self.client:
                raise ProviderError("OpenAI client not initialized")

            # Convert messages to OpenAI format
            openai_messages: List[ChatCompletionMessageParam] = []
            for msg in messages:
                content = msg["content"]["text"]
                msg_type = msg["type"]
                if msg_type == MessageType.QUERY:
                    openai_messages.append(
                        ChatCompletionUserMessageParam(role="user", content=content)
                    )
                elif msg_type == MessageType.RESPONSE:
                    openai_messages.append(
                        ChatCompletionAssistantMessageParam(
                            role="assistant", content=content
                        )
                    )
                elif msg_type == MessageType.COMMAND:
                    openai_messages.append(
                        ChatCompletionSystemMessageParam(role="system", content=content)
                    )

            # Get generation parameters
            model = kwargs.get("model", self.config.model)
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)

            # Generate response
            response = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response text
            text = response.choices[0].message.content or ""

            # Create response object
            return Response(
                id=uuid4(),
                message_id=messages[-1]["id"],
                content={"text": text},
                status=ResponseStatus.SUCCESS,
                metadata={
                    "model": model,
                    "temperature": str(temperature),
                    "max_tokens": str(max_tokens),
                },
            )

        except Exception as e:
            self._logger.error(
                "OpenAI generation failed",
                error=str(e),
                model=self.config.model,
            )
            raise ProviderAPIError(str(e)) from e

    async def stream(
        self, messages: List[Message], **kwargs: Any
    ) -> AsyncIterator[Response]:
        """Stream responses from OpenAI's API.

        Args:
        ----
            messages: List of messages to generate from
            **kwargs: Additional generation parameters

        Returns:
        -------
            An async iterator of response chunks

        Raises:
        ------
            ProviderError: If streaming fails

        """
        self._check_initialized()

        try:
            if not self.client:
                raise ProviderError("OpenAI client not initialized")

            # Convert messages to OpenAI format
            openai_messages: List[ChatCompletionMessageParam] = []
            for msg in messages:
                content = msg["content"]["text"]
                msg_type = msg["type"]
                if msg_type == MessageType.QUERY:
                    openai_messages.append(
                        ChatCompletionUserMessageParam(role="user", content=content)
                    )
                elif msg_type == MessageType.RESPONSE:
                    openai_messages.append(
                        ChatCompletionAssistantMessageParam(
                            role="assistant", content=content
                        )
                    )
                elif msg_type == MessageType.COMMAND:
                    openai_messages.append(
                        ChatCompletionSystemMessageParam(role="system", content=content)
                    )

            # Get generation parameters
            model = kwargs.get("model", self.config.model)
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)

            # Create streaming response
            stream = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            # Stream response chunks
            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                if not delta.content:
                    continue

                yield Response(
                    id=uuid4(),
                    message_id=messages[-1]["id"],
                    content={"text": delta.content},
                    status=ResponseStatus.SUCCESS,
                    metadata={
                        "model": model,
                        "temperature": str(temperature),
                        "max_tokens": str(max_tokens),
                    },
                )

        except Exception as e:
            self._logger.error(
                "OpenAI streaming failed",
                error=str(e),
                model=self.config.model,
            )
            raise ProviderAPIError(str(e)) from e

    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Complete a prompt using OpenAI's API.

        Args:
        ----
            prompt: The prompt to complete
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional completion parameters

        Returns:
        -------
            The completed text or an async generator of text chunks

        Raises:
        ------
            ProviderError: If completion fails

        """
        self._check_initialized()

        try:
            if not self.client:
                raise ProviderError("OpenAI client not initialized")

            # Create message
            message: Message = {
                "id": str(uuid4()),
                "type": MessageType.QUERY,
                "content": {"text": prompt},
            }

            if stream:
                # Stream response chunks
                async def generate_chunks() -> AsyncGenerator[str, None]:
                    async for response in self.stream(
                        [message],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs,
                    ):
                        yield response.content["text"]

                return generate_chunks()
            else:
                # Generate single response
                response = await self.generate(
                    [message],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                return response.content["text"]

        except Exception as e:
            self._logger.error(
                "OpenAI completion failed",
                error=str(e),
                model=self.config.model,
            )
            raise ProviderAPIError(str(e)) from e

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Run a chat completion with the given parameters.

        Args:
        ----
            model: The model to use
            messages: The messages to send to the model
            **kwargs: Additional parameters for the model

        Returns:
        -------
            The model's response

        """
        self._check_initialized()

        try:
            if not self.client:
                raise ProviderError("OpenAI client not initialized")

            # Convert messages to OpenAI format
            openai_messages: List[ChatCompletionMessageParam] = [
                cast(
                    ChatCompletionMessageParam,
                    {"role": msg["role"], "content": msg["content"]},
                )
                for msg in messages
            ]

            response: ChatCompletion = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **kwargs,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            self._logger.error(
                "OpenAI chat completion failed",
                error=str(e),
                model=model,
            )
            raise ProviderAPIError(str(e)) from e
