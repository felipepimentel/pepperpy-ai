"""Base chat module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...ai_types import Message
from ...exceptions import CapabilityError
from ...responses import AIResponse
from ..base import BaseCapability, CapabilityConfig


@dataclass
class ChatConfig(CapabilityConfig):
    """Chat capability configuration."""

    name: str = "chat"
    version: str = "1.0.0"
    enabled: bool = True
    model_name: str = "default"
    device: str = "cpu"
    normalize_embeddings: bool = True
    batch_size: int = 32
    temperature: float = 0.7
    max_tokens: int = 1024
    api_key: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)


class ChatCapability(BaseCapability[ChatConfig], ABC):
    """Base class for chat capabilities."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize chat capability."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup chat capability resources."""
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the chat capability.

        Args:
            messages: The messages to send to the chat capability.
            model: The model to use for generation.
            temperature: The sampling temperature to use.
            max_tokens: The maximum number of tokens to generate.

        Returns:
            An async generator of responses.

        Raises:
            CapabilityError: If capability is not initialized
        """
        if not self.is_initialized:
            raise CapabilityError("Capability not initialized", "chat")
        yield AIResponse(content="Not implemented", provider="chat")
