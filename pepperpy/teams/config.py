"""Team configuration module."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from pepperpy.types import BaseConfig


@dataclass
class BaseTeamConfig:
    """Base team configuration.

    Attributes:
        name: Team name.
        version: Team version.
        provider: Team provider type.
        members: List of team member identifiers.
    """

    name: str
    version: str
    provider: str
    members: Sequence[str]


@dataclass
class TeamConfig(BaseConfig, BaseTeamConfig):
    """Team configuration.

    Attributes:
        name: Team name.
        version: Team version.
        provider: Team provider type.
        members: List of team member identifiers.
        description: Optional team description.
        settings: Optional team-specific settings.
        metadata: Optional metadata about the team.
    """

    description: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TeamResult:
    """Team execution result.

    Attributes:
        success: Whether the execution was successful.
        output: Optional execution output.
        metadata: Optional metadata about the execution.
    """

    success: bool
    output: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
