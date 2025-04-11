"""Agent manager for centralized agent management.

This module provides a centralized manager for agent instances, handling
lifecycle management, persistence, and discovery.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import AgentCapability, AgentContext, BaseAgent, Task
from .registry import AgentRegistry

logger = logging.getLogger(__name__)


class AgentManager:
    """Manager for agent lifecycle and persistence."""

    def __init__(
        self,
        storage_dir: str | None = None,
        memory_type: str = "hierarchical",
        auto_save: bool = True,
        save_interval: int = 300,  # 5 minutes
    ):
        """Initialize the agent manager.

        Args:
            storage_dir: Directory for persistent storage
            memory_type: Type of memory to use
            auto_save: Whether to auto-save agent state
            save_interval: Interval in seconds for auto-save
        """
        self.registry = AgentRegistry()
        self.storage_dir = storage_dir or os.path.expanduser("~/.pepperpy/agents")
        self.memory_type = memory_type
        self.auto_save = auto_save
        self.save_interval = save_interval

        self._auto_save_task = None
        self._is_initialized = False
        self._active_sessions: dict[str, AgentContext] = {}

        # Create storage directory if it doesn't exist
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    async def initialize(self) -> None:
        """Initialize the agent manager."""
        if self._is_initialized:
            return

        # Initialize registry
        await self.registry.initialize({})

        # Load saved agents
        await self._load_agents()

        # Start auto-save task if enabled
        if self.auto_save:
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())

        self._is_initialized = True
        logger.info("Agent manager initialized")

    async def shutdown(self) -> None:
        """Shut down the agent manager."""
        if not self._is_initialized:
            return

        # Save all agents
        if self.auto_save:
            await self.save_all_agents()

        # Cancel auto-save task
        if self._auto_save_task:
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass

        # Shutdown registry
        await self.registry.shutdown()

        self._is_initialized = False
        logger.info("Agent manager shut down")

    async def create_agent(
        self, agent_id: str, agent_type: str, config: dict[str, Any]
    ) -> BaseAgent | None:
        """Create a new agent.

        Args:
            agent_id: Agent ID
            agent_type: Type of agent
            config: Agent configuration

        Returns:
            Created agent or None if creation failed
        """
        agent = await self.registry.create_agent(agent_id, agent_type, config)

        if agent and self.auto_save:
            await self._save_agent(agent)

        return agent

    async def get_agent(self, agent_id: str) -> BaseAgent | None:
        """Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent instance or None if not found
        """
        return await self.registry.get_agent(agent_id)

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent.

        Args:
            agent_id: Agent ID

        Returns:
            True if agent was deleted, False otherwise
        """
        result = await self.registry.delete_agent(agent_id)

        if result:
            # Delete persisted agent data
            agent_file = os.path.join(self.storage_dir, f"{agent_id}.json")
            if os.path.exists(agent_file):
                os.remove(agent_file)

        return result

    async def create_session(
        self, session_id: str, user_id: str | None = None
    ) -> AgentContext:
        """Create a new agent session.

        Args:
            session_id: Session ID
            user_id: User ID

        Returns:
            Agent context for the session
        """
        # Create a new context
        context = AgentContext(session_id=session_id, user_id=user_id)

        # Add to active sessions
        self._active_sessions[session_id] = context

        return context

    async def get_session(self, session_id: str) -> AgentContext | None:
        """Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session context or None if not found
        """
        return self._active_sessions.get(session_id)

    async def end_session(self, session_id: str) -> None:
        """End a session.

        Args:
            session_id: Session ID
        """
        if session_id in self._active_sessions:
            context = self._active_sessions[session_id]
            await context.clear()
            del self._active_sessions[session_id]

    async def get_agents_by_capability(
        self, capability: AgentCapability
    ) -> list[BaseAgent]:
        """Get agents with a specific capability.

        Args:
            capability: Capability to filter by

        Returns:
            List of agents with the capability
        """
        return await self.registry.get_agents_by_capability(capability)

    async def get_agent_types(self) -> list[str]:
        """Get all available agent types.

        Returns:
            List of agent types
        """
        return await self.registry.get_agent_types()

    async def register_agent_type(
        self, type_name: str, agent_class: type[BaseAgent]
    ) -> None:
        """Register a new agent type.

        Args:
            type_name: Type name
            agent_class: Agent class
        """
        await self.registry.register_agent_type(type_name, agent_class)

    async def save_all_agents(self) -> None:
        """Save all agents to persistent storage."""
        for agent_id in await self.registry.get_agent_ids():
            agent = await self.registry.get_agent(agent_id)
            if agent:
                await self._save_agent(agent)

    async def process_task(
        self, task: Task, session_id: str, agent_id: str | None = None
    ) -> Task:
        """Process a task with an agent.

        Args:
            task: Task to process
            session_id: Session ID
            agent_id: Agent ID (optional)

        Returns:
            Processed task

        Raises:
            ValueError: If agent or session not found
        """
        # Get or create session context
        context = self._active_sessions.get(session_id)
        if not context:
            context = await self.create_session(session_id)

        # Get agent
        if agent_id:
            agent = await self.registry.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent not found: {agent_id}")
        else:
            # Find suitable agent based on required capabilities
            suitable_agents = []
            for capability in task.required_capabilities:
                agents = await self.registry.get_agents_by_capability(capability)
                if agents:
                    suitable_agents.extend(agents)

            if not suitable_agents:
                raise ValueError("No suitable agent found for task")

            # Use the first suitable agent
            agent = suitable_agents[0]

        # Process task
        task.agent_id = agent.agent_id
        task.assigned_at = datetime.now()

        try:
            result = await agent.execute(task, context)
            task.result = result
            task.completed_at = datetime.now()
            task.status = task.status  # Keep status from agent
        except Exception as e:
            logger.exception(f"Error executing task: {e!s}")
            task.error = str(e)
            task.status = task.status or "failed"

        return task

    async def get_agent_config(self, agent_id: str) -> dict[str, Any] | None:
        """Get agent configuration.

        Args:
            agent_id: Agent ID

        Returns:
            Agent configuration or None if not found
        """
        agent = await self.registry.get_agent(agent_id)
        if not agent:
            return None

        return agent.to_dict()

    async def update_agent_config(self, agent_id: str, config: dict[str, Any]) -> bool:
        """Update agent configuration.

        Args:
            agent_id: Agent ID
            config: New configuration

        Returns:
            True if successful, False otherwise
        """
        agent = await self.registry.get_agent(agent_id)
        if not agent:
            return False

        # Update configuration
        for key, value in config.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        # Save agent
        if self.auto_save:
            await self._save_agent(agent)

        return True

    async def _load_agents(self) -> None:
        """Load agents from persistent storage."""
        storage_path = Path(self.storage_dir)
        if not storage_path.exists():
            return

        agent_files = list(storage_path.glob("*.json"))
        if not agent_files:
            logger.info("No saved agents found in storage directory")
            return

        logger.info(f"Loading {len(agent_files)} agents from persistent storage")
        for agent_file in agent_files:
            try:
                with open(agent_file) as f:
                    agent_data = json.load(f)

                agent_id = agent_data.get("agent_id")
                agent_type = agent_data.get("type")

                if not agent_id or not agent_type:
                    logger.warning(
                        f"Missing required fields in agent file: {agent_file}"
                    )
                    continue

                # Extract config from agent data
                config = {
                    "name": agent_data.get("name", agent_id),
                    "description": agent_data.get("description", ""),
                }

                # Add type-specific configuration
                if agent_type == "assistant":
                    config["model_id"] = agent_data.get("model_id", "gpt-4")
                    config["system_prompt"] = agent_data.get(
                        "system_prompt", "You are a helpful assistant."
                    )
                    config["max_history_length"] = agent_data.get(
                        "max_history_length", 10
                    )
                elif agent_type == "rag":
                    config["model_id"] = agent_data.get("model_id", "gpt-4")
                    config["vector_store_id"] = agent_data.get(
                        "vector_store_id", "chromadb"
                    )
                    config["max_documents"] = agent_data.get("max_documents", 5)
                elif agent_type == "tool":
                    config["model_id"] = agent_data.get("model_id", "gpt-4")
                    config["available_tools"] = agent_data.get("available_tools", [])

                # Create agent
                agent = await self.registry.create_agent(agent_id, agent_type, config)
                if agent:
                    logger.info(f"Loaded agent {agent_id} of type {agent_type}")

            except Exception as e:
                logger.error(f"Error loading agent from {agent_file}: {e!s}")

    async def _save_agent(self, agent: BaseAgent) -> None:
        """Save agent to persistent storage.

        Args:
            agent: Agent to save
        """
        try:
            # Prepare serializable agent data
            agent_data = agent.to_dict()

            # Add type information
            agent_type = None
            agent_class = agent.__class__.__name__
            for typ, cls in self.registry.agent_types.items():
                if cls.__name__ == agent_class:
                    agent_type = typ
                    break

            if not agent_type:
                logger.warning(f"Could not determine type for agent {agent.agent_id}")
                agent_type = "unknown"

            agent_data["type"] = agent_type

            # Save to file
            agent_file = os.path.join(self.storage_dir, f"{agent.agent_id}.json")
            with open(agent_file, "w") as f:
                json.dump(agent_data, f, indent=2)

            logger.debug(f"Saved agent {agent.agent_id} to {agent_file}")
        except Exception as e:
            logger.error(f"Error saving agent {agent.agent_id}: {e!s}")

    async def _auto_save_loop(self) -> None:
        """Auto-save loop for periodic agent saving."""
        while True:
            try:
                await asyncio.sleep(self.save_interval)
                await self.save_all_agents()
                logger.debug("Auto-saved all agents")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-save loop: {e!s}")


# Singleton instance
_instance = None


def get_agent_manager(
    storage_dir: str | None = None,
    memory_type: str = "hierarchical",
    auto_save: bool = True,
    save_interval: int = 300,
) -> AgentManager:
    """Get the singleton agent manager instance.

    Args:
        storage_dir: Directory for persistent storage
        memory_type: Type of memory to use
        auto_save: Whether to auto-save agent state
        save_interval: Interval in seconds for auto-save

    Returns:
        Agent manager instance
    """
    global _instance
    if _instance is None:
        _instance = AgentManager(storage_dir, memory_type, auto_save, save_interval)
    return _instance
