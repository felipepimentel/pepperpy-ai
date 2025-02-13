"""Type definitions for the Hub package."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TeamRole(str, Enum):
    """Roles that can be assigned to team members."""

    RESEARCHER = "researcher"
    WRITER = "writer"
    REVIEWER = "reviewer"


class TeamMember(BaseModel):
    """Configuration for a team member."""

    name: str
    role: TeamRole
    config: Optional[Dict[str, Any]] = None


class TeamConfig(BaseModel):
    """Configuration for a team."""

    name: str
    description: str
    members: List[TeamMember]
    workflow: str


class Team:
    """A team of agents that can work together on tasks."""

    def __init__(self, config: TeamConfig):
        """Initialize a team with its configuration."""
        self.config = config
        self.name = config.name
        self.members = config.members

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
        self.research = None
        self.article = None
        self.review = None

    async def __aenter__(self):
        """Enter the session context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the session context."""
        self.done = True
        if exc_type:
            self.success = False
            self.error = exc_val
            self.current_status = "Failed"

    async def wait(self):
        """Wait for the session to complete."""
        return self

    async def cancel(self):
        """Cancel the session."""
        self.cancelled = True
        self.success = False
        self.current_status = "Cancelled"
