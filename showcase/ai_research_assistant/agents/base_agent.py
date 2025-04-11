"""Base agent implementation for the AI Research Assistant."""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Task for agent execution."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "default"
    description: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    status: AgentStatus = AgentStatus.IDLE
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    parent_task_id: str | None = None
    subtasks: list[str] = field(default_factory=list)

    def start(self) -> None:
        """Mark task as started."""
        self.status = AgentStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result: dict[str, Any]) -> None:
        """Mark task as completed."""
        self.status = AgentStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()

    def fail(self, error: str) -> None:
        """Mark task as failed."""
        self.status = AgentStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "parent_task_id": self.parent_task_id,
            "subtasks": self.subtasks,
        }


@dataclass
class AgentContext:
    """Context for agent execution."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: dict[str, Any] = field(default_factory=dict)
    shared_memory: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context."""
        self.data[key] = value

    def share(self, key: str, value: Any) -> None:
        """Share a value with other agents."""
        self.shared_memory[key] = value

    def get_shared(self, key: str, default: Any = None) -> Any:
        """Get a shared value."""
        return self.shared_memory.get(key, default)


class BaseAgent(ABC):
    """Base agent for the AI Research Assistant.

    All specialized agents will inherit from this class.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        capabilities: set[str] | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Description of agent's purpose
            capabilities: Set of capabilities the agent has
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities or set()
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the agent's resources."""
        if self.initialized:
            return

        self.status = AgentStatus.INITIALIZING
        try:
            await self._initialize_resources()
            self.initialized = True
            self.status = AgentStatus.IDLE
            self.logger.info(f"Agent {self.name} initialized")
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.logger.error(f"Failed to initialize agent {self.name}: {e}")
            raise

    async def _initialize_resources(self) -> None:
        """Initialize agent-specific resources.

        Override this method in derived classes.
        """
        pass

    async def cleanup(self) -> None:
        """Clean up the agent's resources."""
        if not self.initialized:
            return

        try:
            await self._cleanup_resources()
            self.initialized = False
            self.status = AgentStatus.IDLE
            self.logger.info(f"Agent {self.name} cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up agent {self.name}: {e}")

    async def _cleanup_resources(self) -> None:
        """Clean up agent-specific resources.

        Override this method in derived classes.
        """
        pass

    async def execute(self, task: Task, context: AgentContext) -> Task:
        """Execute a task.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Updated task with results
        """
        if not self.initialized:
            await self.initialize()

        # Mark task as started
        task.start()
        self.status = AgentStatus.RUNNING

        try:
            # Execute task based on type
            result = await self._execute_task(task, context)
            task.complete(result)
            self.status = AgentStatus.COMPLETED
            self.logger.info(f"Task {task.id} completed by agent {self.name}")
        except Exception as e:
            error_msg = str(e)
            task.fail(error_msg)
            self.status = AgentStatus.FAILED
            self.logger.error(
                f"Task {task.id} failed in agent {self.name}: {error_msg}"
            )

        return task

    @abstractmethod
    async def _execute_task(self, task: Task, context: AgentContext) -> dict[str, Any]:
        """Execute agent-specific task logic.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Task result

        Raises:
            Exception: If task execution fails
        """
        pass

    def has_capability(self, capability: str) -> bool:
        """Check if agent has a capability.

        Args:
            capability: Capability to check

        Returns:
            True if agent has capability, False otherwise
        """
        return capability in self.capabilities

    def to_dict(self) -> dict[str, Any]:
        """Convert agent to dictionary.

        Returns:
            Agent as dictionary
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "status": self.status.value,
            "initialized": self.initialized,
        }
