"""Team agent type definitions."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..ai_types import AIMessage

JsonDict = dict[str, Any]


class TeamRole(str, Enum):
    """Team role types."""

    COORDINATOR = "coordinator"
    LEADER = "leader"
    MEMBER = "member"
    SPECIALIST = "specialist"


@dataclass
class TeamMember:
    """Team member configuration."""

    name: str
    role: TeamRole
    metadata: JsonDict = field(default_factory=dict)


@dataclass
class TeamConfig:
    """Team configuration."""

    name: str
    members: list[TeamMember]
    metadata: JsonDict = field(default_factory=dict)


@dataclass
class TeamMessage:
    """Team message."""

    sender: str
    content: str
    role: TeamRole
    metadata: JsonDict = field(default_factory=dict)


@dataclass
class TeamConversation:
    """Team conversation history."""

    messages: list[AIMessage] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)
