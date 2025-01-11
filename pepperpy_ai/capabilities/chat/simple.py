"""Simple chat capability module."""

from typing import Any, Dict, List, Optional

from pepperpy_ai.responses import AIResponse
from pepperpy_ai.capabilities.chat.base import BaseChat, ChatConfig


class SimpleChat(BaseChat):
    """Simple chat capability class."""
    
    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Complete a prompt."""
        return await self.provider.complete(prompt, **kwargs)
    
    async def stream(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Stream responses for a prompt."""
        return await self.provider.stream(prompt, **kwargs) 