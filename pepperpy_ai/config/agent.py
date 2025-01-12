"""Agent configuration module."""

from ..roles import AgentRole
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
        role: str | AgentRole,
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

    def _validate_role(self, role: str | AgentRole) -> AgentRole:
        """Validate and convert role.

        Args:
            role: Role to validate.

        Returns:
            AgentRole: Validated role.

        Raises:
            ValueError: If role is invalid.
        """
        if isinstance(role, AgentRole):
            return role

        valid_roles = {r.value for r in AgentRole}
        if role not in valid_roles:
            raise ValueError(
                f"Invalid role: {role}. Must be one of {sorted(valid_roles)}"
            )
        return AgentRole(role)
