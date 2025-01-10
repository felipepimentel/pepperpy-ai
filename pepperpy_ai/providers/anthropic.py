"""Anthropic provider implementation."""

from collections.abc import AsyncGenerator
from typing import Any, Optional, cast
from datetime import datetime

from anthropic import (
    APIError,
    RateLimitError,
    AuthenticationError,
    APITimeoutError,
)
from anthropic._client import AsyncAnthropic
from anthropic.types import Message, MessageStream

from ..ai_types import AIResponse, AIMessage
from ..llm.base import LLMClient
from ..llm.config import LLMConfig
from .exceptions import (
    ProviderAPIError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from .types import ProviderCapabilities
from ..types import MessageRole

class AnthropicProvider(LLMClient):
    """Anthropic provider implementation."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize provider."""
        super().__init__(config)
        self._client: Optional[AsyncAnthropic] = None
        self._capabilities = ProviderCapabilities(
            streaming=True,
            embeddings=False,  # Anthropic doesn't support embeddings yet
            functions=True,
            max_tokens=100000,  # Claude supports very long contexts
            max_requests_per_minute=50,  # Default Anthropic rate limit
            supports_batch=False,
            batch_size=1
        )

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return self._capabilities

    async def _setup(self) -> None:
        """Setup provider resources."""
        try:
            client = AsyncAnthropic(
                api_key=self.config.api_key,
                timeout=self.config.settings.get("request_timeout", 30.0),
                max_retries=self.config.settings.get("max_retries", 3),
            )
            self._client = cast(AsyncAnthropic, client)
        except Exception as e:
            raise ProviderAPIError(
                "Failed to initialize Anthropic client",
                provider=self.config.provider,
                cause=e
            )

    async def _teardown(self) -> None:
        """Teardown provider resources."""
        if self._client:
            await self._client.close()
            self._client = None

    async def _complete(self, prompt: str) -> AIResponse:
        """Internal completion implementation."""
        if not self._client:
            raise ProviderAPIError(
                "Provider not initialized",
                provider=self.config.provider
            )

        try:
            response = await self._client.messages.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **self.config.settings
            )
            
            message = cast(Message, response)
            return AIResponse(
                content=message.content[0].text,
                messages=[
                    AIMessage(
                        role=MessageRole.ASSISTANT,
                        content=message.content[0].text
                    )
                ],
                metadata={
                    "model": message.model,
                    "stop_reason": message.stop_reason,
                    "usage": {
                        "input_tokens": message.usage.input_tokens,
                        "output_tokens": message.usage.output_tokens
                    }
                }
            )
        except RateLimitError as e:
            raise ProviderRateLimitError(
                provider=self.config.provider,
                retry_after=int(getattr(e, "retry_after", 60))
            )
        except AuthenticationError as e:
            raise ProviderAuthError(
                provider=self.config.provider,
                cause=e
            )
        except APITimeoutError as e:
            raise ProviderTimeoutError(
                provider=self.config.provider,
                timeout=self.config.settings.get("request_timeout", 30.0),
                cause=e
            )
        except APIError as e:
            raise ProviderAPIError(
                str(e),
                provider=self.config.provider,
                status_code=getattr(e, "status_code", None),
                cause=e
            )
        except Exception as e:
            raise ProviderAPIError(
                "Completion failed",
                provider=self.config.provider,
                cause=e
            )

    async def _stream(self, prompt: str) -> AsyncGenerator[AIResponse, None]:
        """Internal streaming implementation."""
        if not self._client:
            raise ProviderAPIError(
                "Provider not initialized",
                provider=self.config.provider
            )

        try:
            stream = await self._client.messages.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
                **self.config.settings
            )

            async for chunk in stream:
                message = cast(MessageStream, chunk)
                if message.delta.text:
                    yield AIResponse(
                        content=message.delta.text,
                        messages=[
                            AIMessage(
                                role=MessageRole.ASSISTANT,
                                content=message.delta.text
                            )
                        ],
                        metadata={
                            "model": message.model,
                            "stop_reason": message.stop_reason,
                            "type": message.type
                        }
                    )
        except RateLimitError as e:
            raise ProviderRateLimitError(
                provider=self.config.provider,
                retry_after=int(getattr(e, "retry_after", 60))
            )
        except AuthenticationError as e:
            raise ProviderAuthError(
                provider=self.config.provider,
                cause=e
            )
        except APITimeoutError as e:
            raise ProviderTimeoutError(
                provider=self.config.provider,
                timeout=self.config.settings.get("request_timeout", 30.0),
                cause=e
            )
        except APIError as e:
            raise ProviderAPIError(
                str(e),
                provider=self.config.provider,
                status_code=getattr(e, "status_code", None),
                cause=e
            )
        except Exception as e:
            raise ProviderAPIError(
                "Streaming failed",
                provider=self.config.provider,
                cause=e
            )
