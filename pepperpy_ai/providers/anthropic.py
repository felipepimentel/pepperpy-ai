"""Anthropic provider implementation."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from anthropic import AsyncAnthropic
from anthropic.types import Message, AsyncMessageStream

from pepperpy_ai.responses import AIResponse
from pepperpy_ai.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Anthropic provider implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229") -> None:
        """Initialize the provider.
        
        Args:
            api_key: Anthropic API key
            model: Model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Complete a prompt.
        
        Args:
            prompt: Prompt to complete
            **kwargs: Additional arguments to pass to the API
            
        Returns:
            AI response
        """
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return AIResponse(content=response.content[0].text)
    
    async def stream(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Stream responses for a prompt.
        
        Args:
            prompt: Prompt to stream
            **kwargs: Additional arguments to pass to the API
            
        Returns:
            AI response
        """
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs,
        )
        content = ""
        async for chunk in response:
            if chunk.type == "content_block_delta":
                content += chunk.delta.text
        return AIResponse(content=content)
