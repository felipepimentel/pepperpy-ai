"""Team management for Pepperpy agents.

This module provides functionality for creating and managing teams of agents
that can work together on complex tasks.
"""

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, TypeVar, cast, runtime_checkable
from uuid import uuid4

from pydantic import BaseModel, Field

from pepperpy.core.base import BaseAgent
from pepperpy.core.client import PepperpyClient
from pepperpy.core.types import Message, MessageType
from pepperpy.hub.agents.base import Agent, AgentSession, AgentStatus
from pepperpy.hub.workflows import Workflow, WorkflowConfig
from pepperpy.monitoring import logger

T = TypeVar("T", bound="Team")


class TeamStatus(Enum):
    """Team execution status."""

    INITIALIZING = auto()  # Team is initializing
    RUNNING = auto()  # Team is executing
    PAUSED = auto()  # Team execution paused
    WAITING = auto()  # Waiting for input/resources
    COMPLETED = auto()  # Successfully completed
    FAILED = auto()  # Execution failed
    CANCELLED = auto()  # Execution cancelled


@dataclass
class TeamProgress:
    """Tracks overall team progress.

    Attributes:
        status: Current team status
        progress: Overall progress (0.0-1.0)
        message: Status message
        active_agents: Currently active agents
        completed_agents: Agents that completed their tasks
        failed_agents: Agents that failed their tasks
        estimated_completion: Estimated completion time

    """

    status: TeamStatus = TeamStatus.INITIALIZING
    progress: float = 0.0
    message: str = ""
    active_agents: List[str] = field(default_factory=list)
    completed_agents: List[str] = field(default_factory=list)
    failed_agents: List[str] = field(default_factory=list)
    estimated_completion: Optional[float] = None

    def update_from_agents(self, sessions: Dict[str, AgentSession]) -> None:
        """Update progress based on agent sessions.

        Args:
            sessions: Map of agent IDs to their sessions

        """
        if not sessions:
            return

        # Reset agent lists
        self.active_agents = []
        self.completed_agents = []
        self.failed_agents = []

        # Calculate overall progress and status
        total_progress = 0.0
        all_completed = True
        any_failed = False

        for agent_id, session in sessions.items():
            # Update agent lists
            if session.progress.status == AgentStatus.COMPLETED:
                self.completed_agents.append(agent_id)
            elif session.progress.status == AgentStatus.FAILED:
                self.failed_agents.append(agent_id)
                any_failed = True
                all_completed = False
            else:
                self.active_agents.append(agent_id)
                all_completed = False

            # Add to total progress
            total_progress += session.progress.progress

        # Update overall progress
        self.progress = total_progress / len(sessions)

        # Update status
        if any_failed:
            self.status = TeamStatus.FAILED
            self.message = f"Failed agents: {', '.join(self.failed_agents)}"
        elif all_completed:
            self.status = TeamStatus.COMPLETED
            self.message = "All agents completed successfully"
        elif any(s.needs_intervention for s in sessions.values()):
            self.status = TeamStatus.WAITING
            self.message = "Waiting for user intervention"
        else:
            self.status = TeamStatus.RUNNING
            self.message = f"Active agents: {', '.join(self.active_agents)}"

        # Update estimated completion
        completion_times = [
            s.progress.estimated_completion
            for s in sessions.values()
            if s.progress.estimated_completion is not None
        ]
        if completion_times:
            self.estimated_completion = max(completion_times)


@dataclass
class TeamSession:
    """Manages a team execution session.

    This class tracks the progress and state of a team of agents working
    together on a task.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    team_id: str = ""
    task: str = ""
    agent_sessions: Dict[str, AgentSession] = field(default_factory=dict)
    progress: TeamProgress = field(default_factory=TeamProgress)
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=lambda: time.time())
    end_time: Optional[float] = None

    @property
    def current_step(self) -> str:
        """Get the current execution step."""
        active_sessions = [
            s
            for s in self.agent_sessions.values()
            if s.progress.status == AgentStatus.RUNNING
        ]
        if active_sessions:
            return active_sessions[0].progress.step
        return ""

    @property
    def thoughts(self) -> List[Dict[str, Any]]:
        """Get all agent thoughts in chronological order."""
        all_thoughts = []
        for agent_id, session in self.agent_sessions.items():
            for thought in session.thoughts:
                all_thoughts.append({
                    "agent": agent_id,
                    "type": thought.type,
                    "content": thought.content,
                    "timestamp": thought.timestamp,
                    **thought.metadata,
                })
        return sorted(all_thoughts, key=lambda x: x["timestamp"])

    @property
    def needs_intervention(self) -> bool:
        """Check if any agent needs intervention."""
        return any(s.needs_intervention for s in self.agent_sessions.values())

    @property
    def intervention_prompts(self) -> Dict[str, str]:
        """Get intervention prompts from agents that need input."""
        return {
            agent_id: session.intervention_prompt
            for agent_id, session in self.agent_sessions.items()
            if session.needs_intervention and session.intervention_prompt
        }

    def provide_intervention(self, agent_id: str, response: str) -> None:
        """Provide intervention response to an agent.

        Args:
            agent_id: ID of the agent to respond to
            response: User's response

        Raises:
            ValueError: If agent doesn't need intervention

        """
        if agent_id not in self.agent_sessions:
            raise ValueError(f"Unknown agent: {agent_id}")

        session = self.agent_sessions[agent_id]
        if not session.needs_intervention:
            raise ValueError(f"Agent {agent_id} doesn't need intervention")

        session.provide_intervention(response)
        self.progress.update_from_agents(self.agent_sessions)

    def record_step_result(self, result: Any) -> None:
        """Record the result of a workflow step.

        Args:
            result: The step execution result

        """
        # Update progress
        self.progress.update_from_agents(self.agent_sessions)

        # Add to metadata
        step_results = self.metadata.setdefault("step_results", [])
        step_results.append({"timestamp": time.time(), "result": result})


class TeamConfig(BaseModel):
    """Configuration for a team.

    Attributes:
        name: Team name
        description: Team description
        agents: List of agent configurations
        workflow: Optional workflow configuration

    """

    name: str
    description: str = "No description provided"
    agents: List[Dict[str, Any]] = Field(default_factory=list)
    workflow: Optional[WorkflowConfig] = None


@runtime_checkable
class TeamProtocol(Protocol):
    """Protocol defining required team methods."""

    async def run(self, task: str, **kwargs: Any) -> Any:
        """Run the team on a task."""
        ...

    async def cleanup(self) -> None:
        """Clean up team resources."""
        ...


class Team(TeamProtocol):
    """A team of agents that can work together.

    Teams provide:
    - Coordinated agent execution
    - Progress monitoring
    - Thought process tracking
    - Resource management
    """

    def __init__(
        self,
        client: PepperpyClient,
        config: TeamConfig,
        agents: Dict[str, BaseAgent],
    ):
        """Initialize a team.

        Args:
            client: The Pepperpy client
            config: Team configuration
            agents: Map of agent names to instances

        """
        self._client = client
        self._config = config
        self._agents = agents
        self._session: Optional[TeamSession] = None
        self.log = logger.bind(team=config.name)

    @classmethod
    async def from_config(cls, client: PepperpyClient, config_path: Path) -> "Team":
        """Create a team from a configuration file.

        Args:
            client: The Pepperpy client
            config_path: Path to team configuration file

        Returns:
            The configured team instance

        Example:
            >>> team = await Team.from_config(client, "path/to/team.yaml")
            >>> async with team.run("Research AI") as session:
            ...     print(session.current_step)
            ...     print(session.thoughts)
            ...     if session.needs_intervention:
            ...         for agent_id, prompt in session.intervention_prompts.items():
            ...             session.provide_intervention(agent_id, "More details")

        """
        import yaml

        with open(config_path) as f:
            raw_config = yaml.safe_load(f)

        config = TeamConfig(**raw_config)

        # Load agents
        agents: Dict[str, BaseAgent] = {}
        for agent_config in config.agents:
            agent_name = agent_config["name"]
            agent = await client.create_agent(agent_name)
            agents[agent_name] = cast(BaseAgent, agent)

        return cls(client, config, agents)

    async def run(self, task: str, **kwargs: Any) -> Any:
        """Run the team on a task.

        Args:
            task: The task to perform
            **kwargs: Additional task parameters

        Returns:
            The final team result

        Example:
            >>> team = await hub.team("research-team")
            >>> async with team.run("Research AI") as session:
            ...     print(session.current_step)
            ...     print(session.thoughts)
            ...     print(session.progress)
            ...     if session.needs_intervention:
            ...         for agent_id, prompt in session.intervention_prompts.items():
            ...             session.provide_intervention(agent_id, "More details")

        """
        # Initialize session
        self._session = TeamSession(team_id=self._config.name, task=task)

        # Initialize agent sessions
        for agent_name, agent in self._agents.items():
            if isinstance(agent, Agent):
                agent_session = await agent.start_session(task)
                self._session.agent_sessions[agent_name] = agent_session

        try:
            # Execute workflow if configured
            if self._config.workflow:
                # Create temporary workflow config file
                import yaml

                temp_config_path = Path("workflows/temp.yaml")
                temp_config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_config_path, "w") as f:
                    yaml.safe_dump(self._config.workflow.to_dict(), f)

                # Create and run workflow
                workflow = await Workflow.from_config(self._client, temp_config_path)
                result = await workflow.run(task, **kwargs)

                # Cleanup temp file
                temp_config_path.unlink()
            else:
                # Default to sequential execution
                result = None
                for agent in self._agents.values():
                    if isinstance(agent, BaseAgent):
                        response = await agent.process_message(
                            Message(
                                id=str(uuid4()),
                                type=MessageType.COMMAND,
                                content={"task": task, **kwargs},
                            )
                        )
                        result = response.content["content"]

            return result

        except Exception as e:
            self.log.error("Team execution failed", error=str(e), task=task, **kwargs)
            raise

        finally:
            # Update end time
            if self._session:
                self._session.end_time = time.time()

    async def cleanup(self) -> None:
        """Clean up team resources."""
        for agent in self._agents.values():
            await agent.cleanup()
        self._session = None

    @property
    def session(self) -> Optional[TeamSession]:
        """Get current session if active."""
        return self._session

    async def __aenter__(self) -> TeamSession:
        """Start a team session.

        Returns:
            A session for monitoring team progress

        Example:
            >>> async with team.run("Research AI") as session:
            ...     print(session.current_step)
            ...     print(session.thoughts)
            ...     print(session.progress)
            ...     if session.needs_intervention:
            ...         for agent_id, prompt in session.intervention_prompts.items():
            ...             session.provide_intervention(agent_id, "More details")

        """
        if not self._session:
            raise RuntimeError("No active session. Call run() first.")
        return self._session

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up team resources."""
        await self.cleanup()


__all__ = ["Team", "TeamConfig", "TeamSession", "TeamProgress", "TeamStatus"]
