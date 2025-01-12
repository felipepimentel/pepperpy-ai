"""Base capability module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from ..ai_types import Message
from ..exceptions import CapabilityError
from ..responses import AIResponse
from ..providers.base import BaseProvider

TConfig = TypeVar("TConfig")

@dataclass
class CapabilityConfig:
    """Base configuration for capabilities."""

    name: str = "capability"
    version: str = "1.0.0"
    enabled: bool = True
    model_name: str = "default"
    device: str = "cpu"
    normalize_embeddings: bool = True
    batch_size: int = 32
    metadata: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)

class BaseCapability(Generic[TConfig], ABC):
    """Base class for capabilities."""

    def __init__(self, config: TConfig, provider: Type[BaseProvider[Any]]) -> None:
        """Initialize capability.

        Args:
            config: Capability configuration
            provider: Provider class to use
        """
        self.config = config
        self.provider = provider
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if capability is initialized."""
        return self._initialized

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize capability."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup capability resources."""
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
        """Stream responses from the capability.

        Args:
            messages: List of messages to send to the provider
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate

        Returns:
            AsyncGenerator yielding AIResponse objects

        Raises:
            CapabilityError: If capability is not initialized
        """
        if not self.is_initialized:
            raise CapabilityError("Capability not initialized", "base")
        yield AIResponse(content="Not implemented", provider="base")
