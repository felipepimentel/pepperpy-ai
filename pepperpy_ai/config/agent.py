"""Agent configuration module."""

from ..core.roles import Role
from .base import BaseConfig


class AgentConfig(BaseConfig):
    """Configuration for agents.

    This class provides configuration options for agents, including their role,
    model settings, and other parameters that control agent behavior.
    """

    def __init__(
        self,
        name: str,
        version: str,
        role: str | Role,
        enabled: bool = True,
    ) -> None:
        """Initialize agent configuration.

        Args:
            name: Agent name.
            version: Agent version.
            role: Agent role.
            enabled: Whether agent is enabled.

        Raises:
            ValueError: If role is invalid.
        """
        super().__init__(name=name, version=version, enabled=enabled)
        self.role = self._validate_role(role)

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
