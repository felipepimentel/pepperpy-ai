"""Agent configuration."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

class AgentRole(str, Enum):
    """Agent role types."""

    ASSISTANT = "assistant"
    USER = "user"
    SYSTEM = "system"

@dataclass
class AgentConfig:
    """Agent configuration."""

    # Required fields
    role: AgentRole

    # Optional fields with defaults
    name: str = "agent"
    version: str = "1.0.0"
    enabled: bool = True
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration."""
        if isinstance(self.role, str):
            try:
                self.role = AgentRole(self.role)
            except ValueError as e:
                raise ValueError(f"Invalid role value: {self.role}. Must be one of {[r.value for r in AgentRole]}") from e
