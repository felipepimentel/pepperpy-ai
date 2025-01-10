"""OpenAI provider implementation."""

from collections.abc import AsyncGenerator
from typing import Any, Optional, cast
from datetime import datetime

from openai._client import AsyncOpenAI
from openai import OpenAIError
from openai.types.chat import ChatCompletion
from openai.types.error import APIError, RateLimitError, AuthenticationError, APITimeoutError

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

class OpenAIProvider(LLMClient):
    """OpenAI provider implementation."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize provider."""
        super().__init__(config)
        self._client: Optional[AsyncOpenAI] = None
        self._capabilities = ProviderCapabilities(
            streaming=True,
            embeddings=True,
            functions=True,
            max_tokens=32000,
            max_requests_per_minute=3500,  # Default OpenAI rate limit
            supports_batch=True,
            batch_size=20
        )

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return self._capabilities

    async def _setup(self) -> None:
        """Setup provider resources."""
        try:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base,
                organization=self.config.settings.get("organization"),
                timeout=self.config.settings.get("request_timeout", 30.0),
                max_retries=self.config.settings.get("max_retries", 3),
            )
        except OpenAIError as e:
            raise ProviderAPIError(
                "Failed to initialize OpenAI client",
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
            response = await self._client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **self.config.settings
            )
            
            completion = cast(ChatCompletion, response)
            return AIResponse(
                content=completion.choices[0].message.content or "",
                messages=[
                    AIMessage(
                        role=MessageRole.ASSISTANT,
                        content=completion.choices[0].message.content or ""
                    )
                ],
                metadata={
                    "model": completion.model,
                    "created": completion.created,
                    "finish_reason": completion.choices[0].finish_reason,
                    "tokens": {
                        "prompt": completion.usage.prompt_tokens,
                        "completion": completion.usage.completion_tokens,
                        "total": completion.usage.total_tokens
                    }
                }
            )
        except RateLimitError as e:
            raise ProviderRateLimitError(
                provider=self.config.provider,
                retry_after=int(getattr(e, "headers", {}).get("retry-after", 60))
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
            stream = await self._client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
                **self.config.settings
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield AIResponse(
                        content=chunk.choices[0].delta.content,
                        messages=[
                            AIMessage(
                                role=MessageRole.ASSISTANT,
                                content=chunk.choices[0].delta.content
                            )
                        ],
                        metadata={
                            "model": chunk.model,
                            "created": chunk.created,
                            "finish_reason": chunk.choices[0].finish_reason
                        }
                    )
        except RateLimitError as e:
            raise ProviderRateLimitError(
                provider=self.config.provider,
                retry_after=int(getattr(e, "headers", {}).get("retry-after", 60))
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

    async def get_embedding(self, text: str) -> list[float]:
        """Get text embedding."""
        if not self._client:
            raise ProviderAPIError(
                "Provider not initialized",
                provider=self.config.provider
            )

        try:
            response = await self._client.embeddings.create(
                model=self.config.model,
                input=text,
                **self.config.settings
            )
            return response.data[0].embedding
        except RateLimitError as e:
            raise ProviderRateLimitError(
                provider=self.config.provider,
                retry_after=int(getattr(e, "headers", {}).get("retry-after", 60))
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
                "Embedding failed",
                provider=self.config.provider,
                cause=e
            )
