"""Team functionality for the Pepperpy Hub."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import yaml

from pepperpy.core.base import BaseAgent
from pepperpy.core.errors import ConfigurationError
from pepperpy.core.types import Message, MessageContent, MessageType, Response
from pepperpy.monitoring import logger

if TYPE_CHECKING:
    from pepperpy.hub import PepperpyHub


class TeamMember:
    """A member of a team with an associated agent."""

    def __init__(
        self,
        name: str,
        role: str,
        agent: BaseAgent,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a team member."""
        self.name = name
        self.role = role
        self.agent = agent
        self.config = config or {}
        self.status = "Initialized"
        self.result: Optional[MessageContent] = None


class Team:
    """A team of agents that can work together on tasks."""

    def __init__(
        self, name: str, description: str, members: List[TeamMember], workflow: str
    ):
        """Initialize a team."""
        self.name = name
        self.description = description
        self.members = members
        self.workflow = workflow
        self.log = logger.bind(component="team", team=name)

    @classmethod
    async def from_config(cls, hub: "PepperpyHub", config_path: Path) -> "Team":
        """Create a team from a configuration file."""
        try:
            # Load team configuration
            config_data = yaml.safe_load(config_path.read_text())

            # Load agents for each member
            members = []
            for member_data in config_data["members"]:
                agent = await hub.agent(
                    member_data["name"],
                    config=member_data.get("config"),
                )
                member = TeamMember(
                    name=member_data["name"],
                    role=member_data["role"],
                    agent=agent,
                    config=member_data.get("config"),
                )
                members.append(member)

            return cls(
                name=config_data["name"],
                description=config_data["description"],
                members=members,
                workflow=config_data["workflow"],
            )

        except Exception as e:
            raise ConfigurationError(f"Failed to load team configuration: {str(e)}")

    async def run(self, task: str) -> "TeamSession":
        """Start a new team session for the given task."""
        return TeamSession(self, task)


class TeamSession:
    """A session representing an active team execution."""

    def __init__(self, team: Team, task: str):
        """Initialize a team session."""
        self.team = team
        self.task = task
        self.done = False
        self.current_status = "Initializing"
        self.success = False
        self.cancelled = False
        self.error = None
        self.research: Optional[MessageContent] = None
        self.article: Optional[MessageContent] = None
        self.review: Optional[MessageContent] = None
        self._tasks = []
        self.log = team.log.bind(session=id(self))

    async def __aenter__(self):
        """Enter the session context."""
        self.log.info("Starting team session", task=self.task)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the session context."""
        self.done = True
        if exc_type:
            self.success = False
            self.error = exc_val
            self.current_status = "Failed"
            self.log.error("Team session failed", error=str(exc_val))
        else:
            self.log.info("Team session completed", success=self.success)

    async def _execute_member(self, member: TeamMember) -> MessageContent:
        """Execute a team member's task."""
        try:
            member.status = "Running"
            self.current_status = f"Running {member.role}"
            self.log.info("Executing member task", role=member.role)

            # Create proper message
            message = Message(
                content={
                    "task": self.task,
                    "role": member.role,
                    "config": member.config,
                },
                type=MessageType.COMMAND,
            )

            # Process message and extract result
            response = await member.agent.process_message(message)
            result = response.content if isinstance(response, Response) else response

            member.status = "Completed"
            member.result = result

            # Store result in appropriate field
            if member.role == "researcher":
                self.research = result
            elif member.role == "writer":
                self.article = result
            elif member.role == "reviewer":
                self.review = result

            return result

        except Exception as e:
            member.status = "Failed"
            self.log.error("Member task failed", role=member.role, error=str(e))
            raise

    async def wait(self) -> "TeamSession":
        """Wait for the session to complete."""
        if not self._tasks:
            # Start tasks in sequence based on roles
            for member in self.team.members:
                if self.cancelled:
                    break
                try:
                    await self._execute_member(member)
                except Exception as e:
                    self.error = e
                    self.current_status = "Failed"
                    self.success = False
                    return self

            if not self.cancelled:
                self.success = True
                self.current_status = "Completed"

        return self

    async def cancel(self):
        """Cancel the session."""
        self.cancelled = True
        self.success = False
        self.current_status = "Cancelled"
        self.log.info("Team session cancelled")
