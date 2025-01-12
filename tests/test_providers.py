"""Test provider functionality."""

from collections.abc import AsyncGenerator
from typing import List, Optional

import pytest

from pepperpy_ai.ai_types import Message
from pepperpy_ai.exceptions import ProviderError
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse


class TestProvider(BaseProvider):
    """Test provider implementation."""

    async def initialize(self) -> None:
        """Initialize test provider."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup test provider."""
        self._initialized = False

    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from test provider.

        Args:
            messages: List of messages to send to provider
            model: Optional model to use
            temperature: Optional temperature parameter
            max_tokens: Optional maximum tokens parameter

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            ProviderError: If provider is not initialized
        """
        if not self.is_initialized:
            raise ProviderError("Provider not initialized", provider="test")
        yield AIResponse(content="test", provider="test", model=model or "test")
