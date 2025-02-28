"""Types and enums for the agents module

Defines the data types and enumerations used in the agents module.
"""

from enum import Enum, auto
from typing import Any, Dict, TypeVar

from pepperpy.common.types.base import BaseComponent

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
