"""Provider types."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..types import JsonDict


class ProviderType(str, Enum):
    """Provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    STACKSPOT = "stackspot"


@dataclass
class ProviderMetadata:
    """Provider metadata."""

    name: str
    version: str
    description: str | None = None
    settings: JsonDict = field(default_factory=dict)


@dataclass
class ProviderResponse:
    """Provider response."""

    content: str
    metadata: JsonDict = field(default_factory=dict)
    raw_response: Any | None = None


@dataclass
class ProviderError:
    """Provider error."""

    message: str
    code: str | None = None
    details: JsonDict = field(default_factory=dict)
    cause: Exception | None = None
