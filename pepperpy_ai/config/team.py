"""Team configuration module."""

from .base import BaseConfig


class TeamConfig(BaseConfig):
    """Configuration for teams.

    This class provides configuration options for teams, including model
    settings, team composition, and other parameters that control team
    behavior.
    """

    def __init__(
        self,
        name: str,
        version: str,
        model: str,
        enabled: bool = True,
        max_members: int = 10,
        max_rounds: int = 5,
        timeout: float = 300.0,
    ) -> None:
        """Initialize team configuration.

        Args:
            name: Team name.
            version: Team version.
            model: Model name or path.
            enabled: Whether team is enabled.
            max_members: Maximum number of team members.
            max_rounds: Maximum number of conversation rounds.
            timeout: Timeout for team operations in seconds.
        """
        super().__init__(name=name, version=version, enabled=enabled)
        self.model = model
        self.max_members = max_members
        self.max_rounds = max_rounds
        self.timeout = timeout
