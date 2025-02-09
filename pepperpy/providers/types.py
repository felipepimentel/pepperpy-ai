"""Type definitions for providers in the Pepperpy framework."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol, TypeAlias, TypedDict, TypeVar

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


class ProviderConfigValue(TypedDict, total=False):
    """Type definition for provider configuration values."""

    value: str | int | float | bool | list[str] | dict[str, str | int | float | bool]
    description: str
    required: bool
    default: str | int | float | bool | None


@dataclass
class ProviderMetadata:
    """Provider metadata."""

    name: str
    version: str
    type: ProviderType
    capabilities: list[ProviderCapability]
    config: dict[str, ProviderConfigValue]


class ProviderConfig(BaseModel):
    """Base configuration for providers."""

    api_key: str | None = None
    api_base: str | None = None
    timeout: float = 30.0
    max_retries: int = 3
    metadata: dict[str, ProviderConfigValue] = {}


T_co = TypeVar("T_co", covariant=True)  # Covariant type for provider responses


class ProviderCallParams(TypedDict, total=False):
    """Type definition for provider call parameters."""

    prompt: str
    messages: list[dict[str, str]]
    model: str
    temperature: float
    max_tokens: int
    stop: list[str]
    stop_sequences: list[str]
    presence_penalty: float
    frequency_penalty: float
    top_p: float
    top_k: int
    stream: bool
    extra_params: dict[str, str | int | float | bool]


# Define base types for provider responses
ProviderScalarValue = str | int | float | bool
ProviderListValue = list[str | float]
ProviderDictValue = dict[str, str | int | float | bool | list[str | float]]

# ruff: noqa: UP040
ProviderResponse: TypeAlias = str | ProviderDictValue | ProviderListValue | T_co


class ProviderProtocol(Protocol[T_co]):
    """Protocol defining the interface for providers."""

    def initialize(self, config: ProviderConfig) -> None:
        """Initialize the provider with configuration.

        Args:
            config: Provider configuration
        """
        ...

    async def call(self, **kwargs: ProviderCallParams) -> ProviderResponse[T_co]:
        """Make a call to the provider.

        Args:
            **kwargs: Provider-specific arguments defined in ProviderCallParams

        Returns:
            Provider response of type ProviderResponse[T_co]
        """
        ...
