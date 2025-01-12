"""Provider configuration."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from pepperpy_core.base import BaseData

from ...types import JsonDict


@dataclass
class ProviderConfig(BaseData):
    """Base provider configuration."""

    provider: str = ""
    model: str = ""
    api_key: str = ""
    api_base: str | None = None
    settings: JsonDict = field(default_factory=dict)


@dataclass
class TeamProviderConfig:
    """Team provider configuration."""

    members: Sequence[str]
    roles: dict[str, str] = field(default_factory=dict)
    tools: dict[str, Any] = field(default_factory=dict)
