"""Team management for Pepperpy agents."""

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Protocol,
    Sequence,
    TypeVar,
    cast,
    runtime_checkable,
)

from pydantic import BaseModel

from pepperpy.core.client import PepperpyClient
from pepperpy.hub.protocols import WorkflowProtocol
from pepperpy.hub.workflows import Workflow

if TYPE_CHECKING:
    from pepperpy.hub.sessions import TeamSession

T = TypeVar("T", bound="Team")


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol defining required agent methods."""

    async def run(self, action: str, **kwargs: Any) -> Any:
        """Run an action on the agent."""
        ...

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        ...


class TeamConfig(BaseModel):
    """Configuration for a team of agents.

    Attributes:
        name: Team name
        agents: List of agent names
        workflow: Optional workflow name

    """

    name: str
    agents: list[str]
    workflow: Optional[str] = None


class Team:
    """A team of agents that can work together.

    Teams can either follow a predefined workflow or operate
    in an ad-hoc manner based on the task.
    """

    def __init__(
        self,
        client: PepperpyClient,
        config: TeamConfig,
        agents: Sequence[AgentProtocol],
        workflow: Optional[WorkflowProtocol] = None,
    ):
        """Initialize a team.

        Args:
            client: The Pepperpy client
            config: Team configuration
            agents: List of agent instances
            workflow: Optional workflow to follow

        """
        self._client = client
        self._config = config
        self._agents = list(agents)
        self._workflow = workflow

    @classmethod
    async def from_config(cls: type[T], client: PepperpyClient, config_path: Path) -> T:
        """Create a team from a configuration file.

        Args:
            client: The Pepperpy client
            config_path: Path to team configuration file

        Returns:
            The configured team instance

        """
        import yaml

        with open(config_path) as f:
            raw_config = yaml.safe_load(f)

        config = TeamConfig(**raw_config)

        # Load agents
        agents = []
        for agent_name in config.agents:
            agent = await client.create_agent(agent_name)
            agents.append(agent)

        # Load workflow if specified
        workflow = None
        if config.workflow:
            workflow_path = (
                config_path.parent.parent / "workflows" / f"{config.workflow}.yaml"
            )
            if workflow_path.exists():
                workflow = await Workflow.from_config(client, workflow_path)
                workflow = cast(WorkflowProtocol, workflow)

        return cls(client, config, agents, workflow)

    async def run(self, task: str, **kwargs: Any) -> Any:
        """Run a task with the team.

        Args:
            task: The task to perform
            **kwargs: Additional task parameters

        Returns:
            The task result

        Example:
            >>> team = await hub.team("research-team")
            >>> async with team.run("Research AI") as session:
            ...     print(session.current_step)

        """
        if self._workflow:
            return await self._workflow.run(task, **kwargs)

        # Default to first agent if no workflow
        return await self._agents[0].run(task, **kwargs)

    async def __aenter__(self) -> "TeamSession":
        """Start a team session.

        Returns:
            A session for monitoring team progress

        """
        from pepperpy.hub.sessions import TeamSession

        return TeamSession(self)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up team resources."""
        for agent in self._agents:
            await agent.cleanup()


__all__ = ["Team", "TeamConfig"]
