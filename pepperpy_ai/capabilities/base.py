"""Base capability module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type, TypeVar

from pepperpy_ai.providers.base import BaseProvider


@dataclass
class CapabilityConfig:
    """Base capability configuration."""
    name: str
    description: str
    version: str = "1.0.0"
    metadata: Optional[Dict[str, str]] = None


T = TypeVar("T")


def register(capability_type: Type[T]) -> Type[T]:
    """Register a capability type."""
    return capability_type


class BaseCapability(ABC):
    """Base capability class."""
    
    def __init__(self, config: CapabilityConfig, provider: BaseProvider) -> None:
        """Initialize the capability."""
        self.config = config
        self.provider = provider
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the capability."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass 