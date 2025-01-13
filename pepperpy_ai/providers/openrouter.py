"""OpenRouter provider implementation."""

import json
import logging
from collections.abc import AsyncGenerator
from typing import NotRequired, TypedDict, cast

import aiohttp

from ..ai_types import Message
from ..responses import AIResponse, ResponseMetadata
from .base import BaseProvider
from .exceptions import ProviderError

logger = logging.getLogger(__name__)


class OpenRouterConfig(TypedDict):
    """OpenRouter provider configuration."""

    model: str  # Required field
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]


class OpenRouterProvider(BaseProvider[OpenRouterConfig]):
    """OpenRouter provider implementation."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, config: OpenRouterConfig, api_key: str) -> None:
        """Initialize provider.

        Args:
            config: Provider configuration
            api_key: OpenRouter API key
        """
        super().__init__(config, api_key)
        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get session instance.

        Returns:
            aiohttp.ClientSession: Session instance.

        Raises:
            ProviderError: If provider is not initialized.
        """
        if not self.is_initialized or not self._session:
            raise ProviderError(
                "Provider not initialized",
                provider="openrouter",
                operation="get_session",
            )
        return self._session

    async def initialize(self) -> None:
        """Initialize provider."""
        if not self._initialized:
            timeout = aiohttp.ClientTimeout(
                total=self.config.get("timeout", 30.0)
            )
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/felipepimentel/pepperpy-ai",
                    "X-Title": "PepperPy AI",
                    "Content-Type": "application/json",
                },
                timeout=timeout,
            )
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        if self._session:
            await self._session.close()
        self._initialized = False
        self._session = None

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from OpenRouter.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized or streaming fails
        """
        if not self.is_initialized:
            raise ProviderError(
                "Provider not initialized",
                provider="openrouter",
                operation="stream",
            )

        try:
            payload = {
                "messages": [
                    {"role": msg.role.value.lower(), "content": msg.content}
                    for msg in messages
                ],
                "model": model or self.config["model"],
                "temperature": temperature or self.config.get("temperature", 0.7),
                "max_tokens": max_tokens or self.config.get("max_tokens", 1000),
                "stream": True,
            }

            logger.debug(
                "Sending request to OpenRouter",
                extra={
                    "provider": "openrouter",
                    "model": payload["model"],
                    "messages": len(messages),
                    "payload": payload,
                },
            )

            async with self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json=payload,
            ) as response:
                if not response.ok:
                    error_text = await response.text()
                    logger.error(
                        "OpenRouter API error",
                        extra={
                            "provider": "openrouter",
                            "status": response.status,
                            "error": error_text,
                        },
                    )
                    raise ProviderError(
                        f"OpenRouter API error: {error_text}",
                        provider="openrouter",
                        operation="stream",
                    )

                logger.debug(
                    "Response headers",
                    extra={
                        "provider": "openrouter",
                        "headers": dict(response.headers),
                    },
                )

                async for line in response.content:
                    try:
                        text = line.decode("utf-8").strip()
                        if not text:
                            continue

                        logger.debug(
                            "Received line",
                            extra={
                                "provider": "openrouter",
                                "line": text,
                            },
                        )

                        if not text.startswith("data: "):
                            continue

                        data_str = text.removeprefix("data: ")
                        if data_str == "[DONE]":
                            continue

                        try:
                            data = json.loads(data_str)
                            if not data["choices"][0]["delta"].get("content"):
                                continue

                            content = data["choices"][0]["delta"]["content"]
                            logger.debug(
                                "Yielding content",
                                extra={
                                    "provider": "openrouter",
                                    "content": content,
                                },
                            )

                            yield AIResponse(
                                content=content,
                                metadata=cast(ResponseMetadata, {
                                    "model": model or self.config["model"],
                                    "provider": "openrouter",
                                    "usage": data.get("usage", {"total_tokens": 0}),
                                    "finish_reason": (
                                        data["choices"][0].get("finish_reason")
                                    ),
                                }),
                            )
                        except json.JSONDecodeError as e:
                            logger.error(
                                "Failed to parse OpenRouter response",
                                extra={
                                    "provider": "openrouter",
                                    "error": str(e),
                                    "data": data_str,
                                },
                            )
                            continue

                    except Exception as e:
                        logger.error(
                            "Error processing response line",
                            extra={
                                "provider": "openrouter",
                                "error": str(e),
                                "line": text if "text" in locals() else line,
                            },
                        )
                        continue

        except ProviderError:
            raise
        except Exception as e:
            logger.error(
                "Failed to stream responses",
                extra={
                    "provider": "openrouter",
                    "error": str(e),
                },
            )
            raise ProviderError(
                f"Failed to stream responses: {e}",
                provider="openrouter",
                operation="stream",
                cause=e,
            ) from e
