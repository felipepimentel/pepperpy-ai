"""Module for multi-agent collaboration capabilities."""

import asyncio
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class AgentRole(Enum):
    """Predefined roles for agents in a collaboration."""

    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"
    CRITIC = "critic"
    MEDIATOR = "mediator"
    OBSERVER = "observer"


@dataclass
class Message:
    """Represents a message between agents."""

    id: str
    sender_id: str
    receiver_id: str
    content: Any
    metadata: Optional[dict] = None


@dataclass
class Task:
    """Represents a task assigned to an agent."""

    id: str
    description: str
    assigned_to: str
    dependencies: Set[str]  # Task IDs that must complete first
    status: str = "pending"
    result: Optional[Any] = None
    metadata: Optional[dict] = None


class Agent:
    """Base class for collaborative agents."""

    def __init__(self, agent_id: str, role: AgentRole):
        self.id = agent_id
        self.role = role
        self.tasks: Dict[str, Task] = {}
        self.message_queue: asyncio.Queue[Message] = asyncio.Queue()

    async def process_message(self, message: Message) -> Optional[Message]:
        """Process an incoming message and optionally generate a response."""
        raise NotImplementedError

    async def execute_task(self, task: Task) -> Any:
        """Execute an assigned task."""
        raise NotImplementedError

    async def run(self):
        """Main agent loop."""
        while True:
            message = await self.message_queue.get()
            response = await self.process_message(message)
            if response:
                await self.send_message(response)

    async def send_message(self, message: Message):
        """Send a message to another agent."""
        # In practice, this would be implemented by the collaboration system
        raise NotImplementedError


class CollaborationSystem:
    """Manages collaboration between multiple agents."""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.message_history: List[Message] = []

    def add_agent(self, agent: Agent):
        """Add an agent to the collaboration."""
        self.agents[agent.id] = agent

    def remove_agent(self, agent_id: str):
        """Remove an agent from the collaboration."""
        if agent_id in self.agents:
            del self.agents[agent_id]

    async def assign_task(self, task: Task):
        """Assign a task to an agent."""
        if task.assigned_to in self.agents:
            self.tasks[task.id] = task
            self.agents[task.assigned_to].tasks[task.id] = task
        else:
            raise ValueError(f"Agent {task.assigned_to} not found")

    async def broadcast_message(
        self, sender_id: str, content: Any, metadata: Optional[dict] = None
    ):
        """Send a message to all agents except the sender."""
        for agent_id, agent in self.agents.items():
            if agent_id != sender_id:
                message = Message(
                    id=str(uuid.uuid4()),
                    sender_id=sender_id,
                    receiver_id=agent_id,
                    content=content,
                    metadata=metadata,
                )
                await agent.message_queue.put(message)
                self.message_history.append(message)

    def get_agent_by_role(self, role: AgentRole) -> List[Agent]:
        """Get all agents with a specific role."""
        return [agent for agent in self.agents.values() if agent.role == role]


class TeamFormation:
    """Manages the formation and organization of agent teams."""

    @dataclass
    class Team:
        """Represents a team of agents."""

        id: str
        name: str
        coordinator: Agent
        members: List[Agent]
        objective: str
        metadata: Optional[dict] = None

    def __init__(self, collaboration_system: CollaborationSystem):
        self.collaboration = collaboration_system
        self.teams: Dict[str, Team] = {}

    def create_team(self, name: str, objective: str) -> Team:
        """Create a new team with appropriate roles."""
        # Find or create a coordinator
        coordinators = self.collaboration.get_agent_by_role(AgentRole.COORDINATOR)
        coordinator = coordinators[0] if coordinators else None

        if not coordinator:
            raise ValueError("No coordinator available")

        # Create the team
        team = self.Team(
            id=str(uuid.uuid4()),
            name=name,
            coordinator=coordinator,
            members=[coordinator],
            objective=objective,
        )

        # Add specialists based on objective
        specialists = self.collaboration.get_agent_by_role(AgentRole.SPECIALIST)
        team.members.extend(specialists)

        # Add a critic
        critics = self.collaboration.get_agent_by_role(AgentRole.CRITIC)
        if critics:
            team.members.append(critics[0])

        self.teams[team.id] = team
        return team

    async def dissolve_team(self, team_id: str):
        """Dissolve a team and reassign its members."""
        if team_id in self.teams:
            del self.teams[team_id]


class Consensus:
    """Manages consensus building between agents."""

    @dataclass
    class Proposal:
        """Represents a proposal for consensus."""

        id: str
        content: Any
        proposer_id: str
        votes: Dict[str, bool]  # agent_id -> vote
        status: str = "pending"
        metadata: Optional[dict] = None

    def __init__(self, collaboration_system: CollaborationSystem):
        self.collaboration = collaboration_system
        self.proposals: Dict[str, Proposal] = {}

    async def submit_proposal(self, proposer_id: str, content: Any) -> Proposal:
        """Submit a new proposal for consensus."""
        proposal = self.Proposal(
            id=str(uuid.uuid4()), content=content, proposer_id=proposer_id, votes={}
        )

        self.proposals[proposal.id] = proposal

        # Notify other agents
        await self.collaboration.broadcast_message(
            sender_id=proposer_id,
            content={
                "type": "proposal",
                "proposal_id": proposal.id,
                "content": content,
            },
        )

        return proposal

    async def vote(self, proposal_id: str, agent_id: str, vote: bool):
        """Record a vote on a proposal."""
        if proposal_id in self.proposals:
            proposal = self.proposals[proposal_id]
            proposal.votes[agent_id] = vote

            # Check if consensus is reached
            if self._check_consensus(proposal):
                proposal.status = (
                    "accepted" if self._is_accepted(proposal) else "rejected"
                )

                # Notify all agents of the result
                await self.collaboration.broadcast_message(
                    sender_id="system",
                    content={
                        "type": "consensus_result",
                        "proposal_id": proposal_id,
                        "status": proposal.status,
                    },
                )

    def _check_consensus(self, proposal: Proposal) -> bool:
        """Check if consensus has been reached."""
        return (
            len(proposal.votes) >= len(self.collaboration.agents) - 1
        )  # Exclude proposer

    def _is_accepted(self, proposal: Proposal) -> bool:
        """Check if proposal is accepted based on votes."""
        positive_votes = sum(1 for vote in proposal.votes.values() if vote)
        return positive_votes >= len(proposal.votes) * 0.7  # 70% majority
