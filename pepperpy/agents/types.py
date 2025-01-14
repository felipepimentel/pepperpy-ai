"""Agent type definitions."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

JsonDict = dict[str, Any]


class AgentRole(Enum):
    """Agent role types."""

    ARCHITECT = auto()
    DEVELOPMENT = auto()
    ANALYSIS = auto()
    PROJECT_MANAGER = auto()
    QA = auto()
    TEAM = auto()
    SPECIALIZED = auto()
    RESEARCH = auto()


@dataclass
class AgentConfig:
    """Agent configuration."""

    name: str
    role: AgentRole
    metadata: JsonDict = field(default_factory=dict)
