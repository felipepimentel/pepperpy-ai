"""Agent configuration management functionality."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pepperpy.common.errors import PepperpyError


class ConfigError(PepperpyError):
    """Configuration error."""
    pass


@dataclass
class AgentCapabilityConfig:
    """Agent capability configuration."""
    
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentStateConfig:
    """Agent state configuration."""
    
    initial_state: str = "initialized"
    valid_states: List[str] = field(
        default_factory=lambda: [
            "initialized",
            "running",
            "paused",
            "stopped",
            "error",
        ]
    )
    valid_transitions: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "initialized": ["running", "stopped"],
            "running": ["paused", "stopped", "error"],
            "paused": ["running", "stopped"],
            "error": ["stopped"],
        }
    )


@dataclass
class AgentConfig:
    """Agent configuration."""
    
    name: str
    description: str
    capabilities: List[AgentCapabilityConfig]
    state: AgentStateConfig = field(default_factory=AgentStateConfig)
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """Validate configuration.
        
        Raises:
            ConfigError: If configuration is invalid
        """
        if not self.name:
            raise ConfigError("Agent name cannot be empty")
            
        if not self.description:
            raise ConfigError("Agent description cannot be empty")
            
        if not self.capabilities:
            raise ConfigError("Agent must have at least one capability")
            
        # Validate state configuration
        if self.state.initial_state not in self.state.valid_states:
            raise ConfigError(
                f"Initial state {self.state.initial_state} not in valid states"
            )
            
        for state in self.state.valid_transitions:
            if state not in self.state.valid_states:
                raise ConfigError(f"Invalid state in transitions: {state}")
                
            for target in self.state.valid_transitions[state]:
                if target not in self.state.valid_states:
                    raise ConfigError(
                        f"Invalid target state in transitions: {target}"
                    )


__all__ = [
    "ConfigError",
    "AgentCapabilityConfig",
    "AgentStateConfig",
    "AgentConfig",
] 