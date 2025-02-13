"""Team management for coordinating AI agents.

This module provides classes for defining and managing teams of AI agents
that work together to complete complex tasks.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    cast,
    runtime_checkable,
)

import yaml
from pydantic import BaseModel, Field
from structlog import get_logger

from pepperpy.core.agents import BaseAgent
from pepperpy.core.types import Message, MessageType
from pepperpy.hub.agents.base import AgentSession, AgentStatus
from pepperpy.hub.session import Session

logger = get_logger()


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
        """Update progress based on agent sessions."""
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
    workflow: Optional[Dict[str, Any]] = None


@runtime_checkable
class TeamProtocol(Protocol):
    """Protocol defining required team methods."""

    async def run(self, task: str, **kwargs: Any) -> Any:
        """Run the team on a task."""
        ...

    async def cleanup(self) -> None:
        """Clean up team resources."""
        ...


@dataclass
class TeamSession:
    """A session for team execution with async context manager support.

    This class provides a way to track team execution progress and manage
    resources properly using async context managers.

    Attributes:
        task: The task being executed
        team: The team executing the task
        context: Shared execution context
        progress: Current execution progress
        current_step: Current execution step
        thoughts: Agent thoughts during execution
        needs_input: Whether user input is needed

    """

    task: str
    team: Team
    context: dict[str, Any]
    progress: TeamProgress = field(default_factory=TeamProgress)
    current_step: str = ""
    thoughts: list[str] = field(default_factory=list)
    needs_input: bool = False
    _session: Optional[Session] = None
    _running_session: Optional[AbstractAsyncContextManager[Session]] = None

    async def __aenter__(self) -> "TeamSession":
        """Enter the async context manager."""
        self._session = Session(
            self.task,
            agent=None,
            workflow=None,
            metadata=self.context,
        )
        self._running_session = self._session.run()
        if self._running_session:
            await self._running_session.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context manager and clean up resources."""
        if self._running_session:
            await self._running_session.__aexit__(exc_type, exc_val, exc_tb)

    def provide_input(self, input_data: str) -> None:
        """Provide input when requested by the team."""
        if not self.needs_input:
            raise RuntimeError("Team is not waiting for input")
        self.context["user_input"] = input_data
        self.needs_input = False

    def add_thought(self, thought: str) -> None:
        """Add a thought to the session history."""
        self.thoughts.append(thought)
        if self._session:
            self._session.add_thought("team", thought)

    def update_progress(self, step: str, progress: float) -> None:
        """Update session progress."""
        self.current_step = step
        self.progress.progress = progress
        if self._session:
            self._session.start_step(step, step, "team")


class Team:
    """A team of AI agents working together.

    Teams provide:
    - Agent coordination
    - Shared context
    - Progress tracking
    - Error handling
    """

    def __init__(
        self,
        name: str,
        agents: list[BaseAgent],
        *,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a team."""
        self.name = name
        self.agents = agents
        self.metadata = metadata or {}

    def run(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> TeamSession:
        """Run the team on a task.

        Args:
            task: The task to perform
            context: Optional shared context
            **kwargs: Additional task parameters

        Returns:
            A TeamSession for monitoring execution

        Example:
            >>> team = await hub.team("research-team")
            >>> async with team.run(
            ...     "Research quantum computing",
            ...     context={"depth": "technical"}
            ... ) as session:
            ...     print(f"Progress: {session.progress}%")
            ...     print(f"Current: {session.current_step}")
            ...     print(f"Thoughts: {session.thoughts}")

        """
        # Create session with context
        session_context = {
            "task": task,
            "team": self.name,
            **(context or {}),
            **kwargs,
        }
        return TeamSession(task=task, team=self, context=session_context)

    async def execute_task(
        self,
        session: TeamSession,
    ) -> Any:
        """Execute task with the team.

        This is the internal method that actually executes the task
        with all team members.

        Args:
            session: The team session to execute in

        Returns:
            The task result

        """
        result = None
        for i, agent in enumerate(self.agents):
            try:
                # Update progress
                step = f"Running agent: {agent.name}"
                session.update_progress(step, (i / len(self.agents)) * 100)

                # Create message with context
                message = Message(
                    content={
                        "task": session.task,
                        "context": session.context,
                    },
                    type=MessageType.COMMAND,
                )

                # Process message and get response
                response = await agent.process_message(message)
                if isinstance(response.content, dict):
                    step_result = response.content.get("result")
                    # Capture thoughts if available
                    thoughts = cast(dict, response.content).get("thoughts")
                    if thoughts:
                        session.add_thought(thoughts)
                else:
                    step_result = response.content

                # Update context and result
                session.context[f"{agent.name}_result"] = step_result
                result = step_result

                # Check if input needed
                if isinstance(response.content, dict) and response.content.get(
                    "needs_input"
                ):
                    session.needs_input = True
                    return result

            except Exception as e:
                logger.error(
                    "Agent execution failed",
                    agent=agent.name,
                    error=str(e),
                )
                raise

        # Update final progress
        session.update_progress("Completed", 100.0)
        return result

    @classmethod
    async def create(
        cls,
        name: str,
        agents: list[str],
        hub: Any,  # PepperpyHub, avoid circular import
        *,
        metadata: dict[str, Any] | None = None,
    ) -> Team:
        """Create a new team with the specified agents.

        Args:
            name: Team name
            agents: List of agent names to load
            hub: The PepperpyHub instance
            metadata: Optional team metadata

        Returns:
            The configured team

        Example:
            >>> team = await Team.create(
            ...     "research",
            ...     ["researcher", "writer"],
            ...     hub
            ... )

        """
        # Load agents from hub
        agent_instances = []
        for agent_name in agents:
            agent = await hub.agent(agent_name)
            agent_instances.append(agent)

        return cls(name, agent_instances, metadata=metadata)

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Team(name='{self.name}', agents={len(self.agents)})"

    @classmethod
    async def from_config(cls, client: Any, config_path: Path) -> Team:
        """Load a team from a configuration file.

        Args:
            client: The PepperpyClient instance
            config_path: Path to the team configuration file

        Returns:
            The loaded team instance

        """
        with open(config_path) as f:
            config = yaml.safe_load(f)

        from pepperpy.hub import PepperpyHub

        hub = PepperpyHub(client)
        return await cls.create(
            name=config["name"],
            agents=[agent["name"] for agent in config.get("agents", [])],
            hub=hub,
            metadata=config.get("metadata", {}),
        )
