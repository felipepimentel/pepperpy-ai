"""Team types module."""

from enum import Enum


class AgentRole(str, Enum):
    """Agent role types."""

    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    ASSISTANT = "assistant"
    USER = "user"
