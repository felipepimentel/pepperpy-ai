"""Tipos e enums para o módulo de agentes

Define os tipos de dados e enumerações utilizados no módulo de agentes.
"""

from enum import Enum, auto
from typing import Any, Dict, TypeVar
from uuid import UUID

from pepperpy.core.types.base import BaseComponent
from pepperpy.core.types.enums import AgentID, AgentState

from .base import BaseAgent


class AgentKind(Enum):
    """Types of agents."""

    AUTONOMOUS = auto()
    INTERACTIVE = auto()
    TASK_ASSISTANT = auto()


# Type aliases
AgentConfig = Dict[str, Any]
AgentResult = Dict[str, Any]

# Type variables
T = TypeVar("T", bound=BaseComponent)
AgentT = TypeVar("AgentT", bound=BaseAgent)
