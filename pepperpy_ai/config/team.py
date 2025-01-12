"""Team configuration."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class TeamConfig:
    """Team configuration."""

    # Required fields
    members: List[str]
    roles: Dict[str, str]

    # Optional fields with defaults
    name: str = "team"
    version: str = "1.0.0"
    enabled: bool = True
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.members:
            raise ValueError("Team must have at least one member")
        if not self.roles:
            raise ValueError("Team must have at least one role")
