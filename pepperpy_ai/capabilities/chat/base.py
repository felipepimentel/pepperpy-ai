"""Base chat capability module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar

from pepperpy_ai.responses import AIResponse
from pepperpy_ai.capabilities.base import BaseCapability


@dataclass
class ChatConfig:
    """Chat capability configuration."""
    model_name: str
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None


class BaseChat(BaseCapability):
    """Base chat capability class."""
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Complete a prompt."""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Stream responses for a prompt."""
        pass 