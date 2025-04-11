"""Agent manager module for AI Gateway.

This module provides functionality for managing agents, including:
- Agent registry
- Agent lifecycle
- Task routing and assignment
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from .base import (
    AgentCapability,
    AgentContext,
    BaseAgent,
    Task,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages agents and tasks."""

    def __init__(self):
        """Initialize agent manager."""
        self.agents: dict[str, BaseAgent] = {}
        self.agent_context = AgentContext()
        self.task_queue: asyncio.Queue[Task] = asyncio.Queue()
        self.task_history: dict[str, Task] = {}
        self._running = False
        self._worker_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent.

        Args:
            agent: Agent to register
        """
        async with self._lock:
            if agent.id in self.agents:
                logger.warning(f"Agent already registered: {agent.id}")
                return

            self.agents[agent.id] = agent

            if not agent.is_initialized:
                try:
                    await agent.initialize(self.agent_context)
                except Exception as e:
                    logger.error(f"Failed to initialize agent {agent.id}: {e}")
                    del self.agents[agent.id]
                    raise

            logger.info(
                f"Registered agent: {agent.name} ({agent.id}) with "
                f"capabilities: {[c.value for c in agent.capabilities]}"
            )

    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent.

        Args:
            agent_id: ID of agent to unregister
        """
        async with self._lock:
            if agent_id not in self.agents:
                logger.warning(f"Agent not registered: {agent_id}")
                return

            agent = self.agents[agent_id]

            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Failed to clean up agent {agent_id}: {e}")

            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent.name} ({agent_id})")

    def get_agent(self, agent_id: str) -> BaseAgent | None:
        """Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent or None if not found
        """
        return self.agents.get(agent_id)

    def list_agents(self) -> list[BaseAgent]:
        """List all registered agents.

        Returns:
            List of agents
        """
        return list(self.agents.values())

    async def find_agents_by_capability(
        self, capability: AgentCapability
    ) -> list[BaseAgent]:
        """Find agents with a capability.

        Args:
            capability: Capability to search for

        Returns:
            List of agents with the capability
        """
        return [
            agent for agent in self.agents.values() if agent.has_capability(capability)
        ]

    async def find_agents_by_capabilities(
        self, capabilities: list[AgentCapability]
    ) -> list[BaseAgent]:
        """Find agents with all capabilities.

        Args:
            capabilities: Capabilities to search for

        Returns:
            List of agents with all capabilities
        """
        return [
            agent
            for agent in self.agents.values()
            if agent.has_capabilities(capabilities)
        ]

    async def enqueue_task(self, task: Task) -> None:
        """Enqueue a task for execution.

        Args:
            task: Task to enqueue
        """
        self.task_history[task.id] = task
        await self.task_queue.put(task)
        logger.info(
            f"Enqueued task: {task.id} - {task.objective} "
            f"(priority: {task.priority.value})"
        )

    async def assign_task(self, task: Task, agent_id: str) -> None:
        """Assign a task to a specific agent.

        Args:
            task: Task to assign
            agent_id: ID of agent to assign task to

        Raises:
            ValueError: If agent not found or cannot handle task
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent not found: {agent_id}")

        agent = self.agents[agent_id]

        task.agent_id = agent_id
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.now()

        logger.info(f"Assigned task {task.id} to agent: {agent.name} ({agent_id})")

        # Process task asynchronously
        asyncio.create_task(self._process_task(task, agent))

    async def _process_task(self, task: Task, agent: BaseAgent) -> None:
        """Process a task with an agent.

        Args:
            task: Task to process
            agent: Agent to process task
        """
        try:
            await agent.process_task(task, self.agent_context)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            logger.error(f"Error processing task {task.id}: {e}", exc_info=True)

    async def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task or None if not found
        """
        return self.task_history.get(task_id)

    async def start(self) -> None:
        """Start the agent manager."""
        async with self._lock:
            if self._running:
                return

            self._running = True
            self._worker_task = asyncio.create_task(self._worker())

            logger.info("Agent manager started")

    async def stop(self) -> None:
        """Stop the agent manager."""
        async with self._lock:
            if not self._running:
                return

            self._running = False

            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass

                self._worker_task = None

            # Clean up agents
            for agent_id in list(self.agents.keys()):
                await self.unregister_agent(agent_id)

            logger.info("Agent manager stopped")

    async def _worker(self) -> None:
        """Worker task for processing queued tasks."""
        try:
            while self._running:
                # Get task
                task = await self.task_queue.get()

                if task.status != TaskStatus.PENDING:
                    self.task_queue.task_done()
                    continue

                # Find suitable agent
                suitable_agents = [
                    agent
                    for agent in self.agents.values()
                    if agent.is_initialized and not hasattr(agent, "_current_task")
                ]

                if not suitable_agents:
                    # No suitable agents, requeue task
                    await self.task_queue.put(task)
                    await asyncio.sleep(1)
                    self.task_queue.task_done()
                    continue

                # Choose agent (simple round-robin for now)
                agent = suitable_agents[0]

                # Assign task
                await self.assign_task(task, agent.id)

                self.task_queue.task_done()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Worker task error: {e}", exc_info=True)
            if self._running:
                # Restart worker
                self._worker_task = asyncio.create_task(self._worker())


class AgentRegistry:
    """Registry for agent types."""

    _instance = None

    def __new__(cls):
        """Create singleton instance.

        Returns:
            AgentRegistry
        """
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize agent registry."""
        if self._initialized:
            return

        self.agent_factories: dict[str, Any] = {}
        self._initialized = True

    def register_factory(self, agent_type: str, factory: Any) -> None:
        """Register an agent factory.

        Args:
            agent_type: Agent type
            factory: Agent factory
        """
        self.agent_factories[agent_type] = factory
        logger.info(f"Registered agent factory: {agent_type}")

    def unregister_factory(self, agent_type: str) -> None:
        """Unregister an agent factory.

        Args:
            agent_type: Agent type
        """
        if agent_type in self.agent_factories:
            del self.agent_factories[agent_type]
            logger.info(f"Unregistered agent factory: {agent_type}")

    def create_agent(self, agent_type: str, **kwargs: Any) -> BaseAgent:
        """Create an agent.

        Args:
            agent_type: Agent type
            **kwargs: Agent parameters

        Returns:
            Agent

        Raises:
            ValueError: If agent type not registered
        """
        if agent_type not in self.agent_factories:
            raise ValueError(f"Agent type not registered: {agent_type}")

        factory = self.agent_factories[agent_type]

        if callable(factory):
            return factory(**kwargs)

        raise ValueError(f"Invalid agent factory: {agent_type}")

    def get_factory(self, agent_type: str) -> Any:
        """Get an agent factory.

        Args:
            agent_type: Agent type

        Returns:
            Agent factory

        Raises:
            ValueError: If agent type not registered
        """
        if agent_type not in self.agent_factories:
            raise ValueError(f"Agent type not registered: {agent_type}")

        return self.agent_factories[agent_type]

    def list_agent_types(self) -> list[str]:
        """List all registered agent types.

        Returns:
            List of agent types
        """
        return list(self.agent_factories.keys())
