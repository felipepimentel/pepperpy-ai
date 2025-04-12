"""
A2A Simulation Environment.

This module provides a simulation environment for testing A2A protocol
interactions between multiple agents without requiring external services.
"""

import asyncio
import uuid
from collections.abc import Callable
from typing import Any

from pepperpy.a2a.base import (
    A2AError,
    AgentCard,
    Message,
    Task,
    TaskState,
    TextPart,
)
from pepperpy.a2a.providers import create_text_message
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class SimulationError(A2AError):
    """Error in simulation environment."""

    pass


class SimulatedAgent:
    """A simulated agent in the A2A protocol.

    This class represents an agent that can receive and respond to messages.
    """

    def __init__(
        self,
        agent_id: str,
        agent_card: AgentCard,
        response_handler: Callable[..., Any],
    ) -> None:
        """Initialize a simulated agent.

        Args:
            agent_id: Unique identifier for the agent
            agent_card: Agent card with capabilities
            response_handler: Function to handle incoming messages and generate responses.
                Can be either synchronous or asynchronous.
        """
        self.agent_id = agent_id
        self.agent_card = agent_card
        self.response_handler = response_handler
        self.tasks: dict[str, Task] = {}

    async def process_message(self, task_id: str, message: Message) -> Message:
        """Process an incoming message and generate a response.

        Args:
            task_id: Task ID
            message: Incoming message

        Returns:
            Response message
        """
        # Call the response handler to generate a response
        return await self._call_response_handler(message)

    async def _call_response_handler(self, message: Message) -> Message:
        """Call the response handler function.

        Args:
            message: Incoming message

        Returns:
            Response message
        """
        if asyncio.iscoroutinefunction(self.response_handler):
            response = await self.response_handler(message)
        else:
            response = self.response_handler(message)

        # Ensure we have a valid Message object
        if not isinstance(response, Message):
            if isinstance(response, str):
                # Convert string to a text message
                response = create_text_message("agent", response)
            else:
                raise SimulationError(
                    f"Invalid response handler result: {type(response)}, must return Message or str"
                )

        return response


class SimulationEnvironment:
    """A2A protocol simulation environment.

    This class provides a simulation environment for testing A2A protocol
    interactions between multiple agents.
    """

    def __init__(self) -> None:
        """Initialize the simulation environment."""
        self.agents: dict[str, SimulatedAgent] = {}
        self.tasks: dict[str, Task] = {}
        self.agent_ids_by_name: dict[str, str] = {}
        self.tasks_by_agent: dict[str, set[str]] = {}

    def register_agent(
        self,
        agent_id: str | None = None,
        name: str = "Simulated Agent",
        description: str = "A simulated agent",
        capabilities: list[str] | None = None,
        response_handler: Callable[..., Any] | None = None,
    ) -> tuple[str, AgentCard]:
        """Register a simulated agent.

        Args:
            agent_id: Optional agent ID (generated if None)
            name: Agent name
            description: Agent description
            capabilities: Agent capabilities
            response_handler: Function to handle incoming messages.
                Can be either synchronous or asynchronous.

        Returns:
            Tuple of (agent_id, agent_card)

        Raises:
            SimulationError: If agent with the same name already exists
        """
        if name in self.agent_ids_by_name:
            raise SimulationError(f"Agent with name '{name}' already exists")

        # Generate agent ID if not provided
        if agent_id is None:
            agent_id = str(uuid.uuid4())

        # Default capabilities
        if capabilities is None:
            capabilities = ["text-generation"]

        # Default response handler just echoes the message
        if response_handler is None:

            def echo_handler(message: Message) -> Message:
                text_parts = [
                    part.text for part in message.parts if isinstance(part, TextPart)
                ]
                text = " ".join(text_parts)
                return create_text_message("agent", f"Echo: {text}")

            response_handler = echo_handler

        # Create agent card
        agent_card = AgentCard(
            name=name,
            description=description,
            endpoint=f"sim://{agent_id}",
            capabilities=capabilities,
        )

        # Create and register the agent
        agent = SimulatedAgent(agent_id, agent_card, response_handler)
        self.agents[agent_id] = agent
        self.agent_ids_by_name[name] = agent_id
        self.tasks_by_agent[agent_id] = set()

        logger.debug(f"Registered simulated agent: {name} ({agent_id})")
        return agent_id, agent_card

    def get_agent_by_name(self, name: str) -> SimulatedAgent | None:
        """Get a simulated agent by name.

        Args:
            name: Agent name

        Returns:
            Simulated agent or None if not found
        """
        agent_id = self.agent_ids_by_name.get(name)
        if agent_id:
            return self.agents.get(agent_id)
        return None

    def get_agent_id_by_name(self, name: str) -> str | None:
        """Get agent ID by name.

        Args:
            name: Agent name

        Returns:
            Agent ID or None if not found
        """
        return self.agent_ids_by_name.get(name)

    async def send_message(
        self,
        agent_id: str,
        message: Message,
        task_id: str | None = None,
    ) -> Task:
        """Send a message to a simulated agent.

        Args:
            agent_id: Target agent ID
            message: Message to send
            task_id: Optional task ID (new task created if None)

        Returns:
            Updated task

        Raises:
            SimulationError: If agent not found or task not found
        """
        # Check if agent exists
        agent = self.agents.get(agent_id)
        if not agent:
            raise SimulationError(f"Agent not found: {agent_id}")

        # Get or create task
        if task_id is None:
            # Create a new task
            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                state=TaskState.SUBMITTED,
                messages=[message],
                artifacts=[],
                metadata={"agent_id": agent_id},
            )
            self.tasks[task_id] = task
            self.tasks_by_agent[agent_id].add(task_id)
        else:
            # Get existing task
            task = self.tasks.get(task_id)
            if not task:
                raise SimulationError(f"Task not found: {task_id}")

            # Update task with new message
            task.messages.append(message)
            task.state = TaskState.WORKING

        # Process the message
        response = await agent.process_message(task_id, message)

        # Update task with response
        task.messages.append(response)
        task.state = TaskState.COMPLETED

        return task

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task or None if not found
        """
        return self.tasks.get(task_id)

    def get_tasks_for_agent(self, agent_id: str) -> list[Task]:
        """Get all tasks for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of tasks
        """
        task_ids = self.tasks_by_agent.get(agent_id, set())
        return [self.tasks[task_id] for task_id in task_ids if task_id in self.tasks]

    def clear(self) -> None:
        """Clear the simulation environment."""
        self.agents.clear()
        self.tasks.clear()
        self.agent_ids_by_name.clear()
        self.tasks_by_agent.clear()
        logger.debug("Cleared simulation environment")


async def create_simulation() -> SimulationEnvironment:
    """Create a new simulation environment.

    Returns:
        Initialized simulation environment
    """
    return SimulationEnvironment()


# Example response handlers
def simple_echo_handler(message: Message) -> Message:
    """Simple echo response handler.

    Args:
        message: Incoming message

    Returns:
        Echo response message
    """
    text_parts = [part.text for part in message.parts if isinstance(part, TextPart)]
    text = " ".join(text_parts)
    return create_text_message("agent", f"Echo: {text}")


async def delayed_response_handler(message: Message) -> Message:
    """Delayed response handler with simulated thinking.

    Args:
        message: Incoming message

    Returns:
        Response message after delay
    """
    # Simulate processing time
    await asyncio.sleep(1.0)

    text_parts = [part.text for part in message.parts if isinstance(part, TextPart)]
    text = " ".join(text_parts)
    return create_text_message("agent", f"After thinking, I respond: {text}")


class StatefulResponseHandler:
    """Stateful response handler that remembers conversation context."""

    def __init__(self) -> None:
        """Initialize the stateful response handler."""
        self.context: list[tuple[str, str]] = []

    async def __call__(self, message: Message) -> Message:
        """Process an incoming message.

        Args:
            message: Incoming message

        Returns:
            Response message
        """
        # Extract text
        text_parts = [part.text for part in message.parts if isinstance(part, TextPart)]
        text = " ".join(text_parts)

        # Add to context
        self.context.append(("user", text))

        # Generate response based on context
        response = f"I've recorded {len(self.context)} messages so far. Your last message was: {text}"

        # Add response to context
        self.context.append(("agent", response))

        return create_text_message("agent", response)
