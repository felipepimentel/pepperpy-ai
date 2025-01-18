"""Main application module."""

import os
from typing import Any

import yaml

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.agents.registry.factory import AgentFactory
from pepperpy.data_stores.document_store import DocumentStore
from pepperpy.llms.llm_manager import LLMManager
from pepperpy.llms.token_handler import TokenHandler


class PepperPy:
    """Main application class."""

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize PepperPy.

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.llm_manager = LLMManager()
        self.agent_factory = AgentFactory()
        self.document_store = DocumentStore(self.config.get("document_store", {}))
        self.token_handler = TokenHandler()
        self.is_initialized = False

    def _load_config(self, config_path: str | None) -> dict[str, Any]:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        if not config_path:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "default.yaml"
            )

        with open(config_path) as f:
            return yaml.safe_load(f)

    async def initialize(self) -> None:
        """Initialize application components.

        This includes:
        - Setting up logging
        - Initializing LLM manager
        - Setting up document store
        - Loading agent configurations
        """
        if self.is_initialized:
            return

        try:
            await self.llm_manager.initialize(self.config.get("llm", {}))
            await self.document_store.setup()
            self.is_initialized = True
        except Exception as e:
            raise Exception(f"Failed to initialize PepperPy: {e!s}") from e

    async def create_agent(self, agent_type: str, config: dict[str, Any]) -> BaseAgent:
        """Create an agent instance.

        Args:
            agent_type: Type of agent to create
            config: Agent configuration

        Returns:
            Agent instance

        Raises:
            ValueError: If agent type is invalid
        """
        if not self.is_initialized:
            raise ValueError("PepperPy not initialized")

        return await self.agent_factory.create_agent(agent_type, config)

    async def cleanup(self) -> None:
        """Clean up application resources.

        This includes:
        - Closing document store
        - Cleaning up LLM manager
        - Releasing agent resources
        """
        if not self.is_initialized:
            return

        try:
            await self.document_store.cleanup()
            await self.llm_manager.cleanup()
            self.is_initialized = False
        except Exception as e:
            raise Exception(f"Failed to clean up PepperPy: {e!s}") from e

    async def __aenter__(self) -> "PepperPy":
        """Context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.cleanup()
