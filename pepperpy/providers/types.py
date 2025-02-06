"""Type definitions for providers in the Pepperpy framework."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Protocol, TypeAlias, TypeVar

from pydantic import BaseModel


class ProviderType(Enum):
    """Types of providers."""

    LLM = auto()
    EMBEDDING = auto()
    STORAGE = auto()
    SEARCH = auto()
    CUSTOM = auto()


class ProviderCapability(Enum):
    """Provider capabilities."""

    TEXT_GENERATION = auto()
    CODE_GENERATION = auto()
    EMBEDDING = auto()
    CLASSIFICATION = auto()
    SUMMARIZATION = auto()
    TRANSLATION = auto()
    CUSTOM = auto()


@dataclass
class ProviderMetadata:
    """Provider metadata."""

    name: str
    version: str
    type: ProviderType
    capabilities: list[ProviderCapability]
    config: dict[str, Any]


class ProviderConfig(BaseModel):
    """Base configuration for providers."""

    api_key: str | None = None
    api_base: str | None = None
    timeout: float = 30.0
    max_retries: int = 3
    metadata: dict[str, Any] = {}


T_co = TypeVar("T_co", covariant=True)
# ruff: noqa: UP040
ProviderResponse: TypeAlias = str | dict[str, Any] | list[Any] | T_co


class ProviderProtocol(Protocol[T_co]):
    """Protocol defining the interface for providers."""

    def initialize(self, config: ProviderConfig) -> None:
        """Initialize the provider with configuration.

        Args:
            config: Provider configuration
        """
        ...

    async def call(self, **kwargs: Any) -> ProviderResponse:
        """Make a call to the provider.

        Args:
            **kwargs: Provider-specific arguments

        Returns:
            Provider response
        """
        ...
