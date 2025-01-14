"""Agent configuration module."""

from dataclasses import dataclass

from pepperpy.core.roles import Role
from pepperpy.types import BaseConfig


@dataclass
class BaseAgentConfig:
    """Base agent configuration.

    Attributes:
        name: Agent name.
        version: Agent version.
        provider: Agent provider type.
    """

    name: str
    version: str
    provider: str


@dataclass
class AgentConfig(BaseConfig, BaseAgentConfig):
    """Agent configuration.

    This class provides configuration options for agents, including their role,
    model settings, and other parameters that control agent behavior.

    Attributes:
        name: Agent name.
        version: Agent version.
        provider: Agent provider type.
        role: Agent role.
        description: Optional agent description.
        settings: Optional agent-specific settings.
        metadata: Optional metadata about the agent.
    """

    role: Role | None = None
    description: str | None = None

    def _validate_role(self, role: str | Role) -> Role:
        """Validate and convert role.

        Args:
            role: Role to validate.

        Returns:
            Role: Validated role.

        Raises:
            ValueError: If role is invalid.
            TypeError: If role is not a string or Role instance.
        """
        if isinstance(role, Role):
            return role

        if not isinstance(role, str):
            raise TypeError("Role must be a string or Role instance")

        # Create role from string
        return Role(
            name=role,
            description="",  # These will be populated by the agent
            instructions="",  # These will be populated by the agent
        )
