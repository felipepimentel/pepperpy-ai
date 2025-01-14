"""Team configuration module."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from pepperpy_core.types import BaseConfig


@dataclass
class TeamConfig(BaseConfig):
    """Team configuration."""

    name: str
    version: str
    provider: str
    members: Sequence[str]
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TeamResult:
    """Team execution result."""

    success: bool
    output: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
