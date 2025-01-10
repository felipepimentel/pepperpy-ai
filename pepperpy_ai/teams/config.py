"""Team configuration."""

from collections.abc import Sequence
from dataclasses import dataclass, field

from ..types import JsonDict


@dataclass
class TeamConfig:
    """Team configuration."""

    name: str
    provider: str
    members: Sequence[str]
    settings: JsonDict = field(default_factory=dict)
    metadata: JsonDict = field(default_factory=dict)


@dataclass
class TeamResult:
    """Team execution result."""

    success: bool
    output: str | None = None
    metadata: JsonDict = field(default_factory=dict)
