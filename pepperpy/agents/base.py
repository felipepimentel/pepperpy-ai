"""Base agent functionality.

This module provides base classes and utilities for agent implementation,
including configuration, memory management, and monitoring.
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol

from pydantic import BaseModel

from pepperpy.core.errors import (
    ConfigError,
)
from pepperpy.core.resources import Resource
from pepperpy.hub.resource_manager import get_resource_manager
from pepperpy.memory.simple import SimpleMemory

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class AgentConfig(BaseModel):
    """Agent configuration.

    Attributes:
        name: Agent name
        description: Agent description
        parameters: Agent parameters
        metadata: Additional metadata
    """

    name: str
    description: str = ""
    parameters: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class AgentMessage(BaseModel):
    """Message exchanged with an agent.

    Attributes:
        role: Message role (e.g. "user", "assistant")
        content: Message content
        metadata: Additional metadata
    """

    role: str
    content: str
    metadata: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    """Response from an agent.

    Attributes:
        messages: List of messages in the response
        metadata: Additional metadata
    """

    messages: List[AgentMessage]
    metadata: Dict[str, Any] = {}


class AgentProvider(Protocol):
    """Protocol for agent providers."""

    async def create(self, config: AgentConfig, **kwargs: Any) -> str:
        """Create a new agent.

        Args:
            config: Agent configuration
            **kwargs: Additional provider-specific parameters

        Returns:
            Agent ID

        Raises:
            AgentError: If creation fails
        """
        ...

    async def execute(
        self,
        agent_id: str,
        messages: List[AgentMessage],
        **kwargs: Any,
    ) -> AgentResponse:
        """Execute an agent.

        Args:
            agent_id: Agent ID to execute
            messages: Messages to process
            **kwargs: Additional provider-specific parameters

        Returns:
            Agent response

        Raises:
            AgentError: If execution fails
        """
        ...

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        ...


class AgentExtension:
    """Concrete extension class for agents."""

    def __init__(
        self,
        name: str,
        version: str,
        config: Optional[AgentConfig] = None,
    ) -> None:
        """Initialize agent extension."""
        from pepperpy.core.extensions import Extension

        class ConcreteExtension(Extension[AgentConfig]):
            async def _initialize(self) -> None:
                pass

            async def _cleanup(self) -> None:
                pass

        self._extension = ConcreteExtension(name, version, config)


class BaseAgent:
    """Base class for agents.

    This class defines the interface that all agents must implement.
    """

    def __init__(
        self,
        name: str,
        version: str,
        config: Optional[AgentConfig] = None,
    ) -> None:
        """Initialize agent.

        Args:
            name: Agent name
            version: Agent version
            config: Optional agent configuration
        """
        self._extension = AgentExtension(name, version, config)._extension
        self._name = name
        self._version = version
        self._config = config

    @property
    def metadata(self):
        """Get agent metadata."""
        return self._extension.metadata

    async def initialize(self) -> None:
        """Initialize agent."""
        await self._extension.initialize()
        await self._initialize()

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        await self._cleanup()
        await self._extension.cleanup()

    async def get_capabilities(self) -> List[str]:
        """Get list of capabilities provided.

        Returns:
            List of capability identifiers
        """
        return [self.metadata.name]

    async def get_dependencies(self) -> List[str]:
        """Get list of required dependencies.

        Returns:
            List of dependency identifiers
        """
        return []

    async def _initialize(self) -> None:
        """Initialize agent resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up agent resources."""
        pass


class Agent(Resource, ABC):
    """Base class for all agents.

    This class provides common functionality for agents including:
    - Configuration management
    - Memory management
    - Resource lifecycle
    - Error handling
    """

    def __init__(
        self,
        config_name: Optional[str] = None,
        config_version: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize agent with configuration.

        Args:
            config_name: Name of the configuration to load from Hub
            config_version: Version of the configuration to load
            **kwargs: Additional configuration options

        Raises:
            ConfigError: If configuration loading fails
        """
        # Define default configuration
        self.default_config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
            "memory": {
                "enabled": True,
                "type": "simple",
                "config": {
                    "auto_cleanup": True,
                    "cleanup_interval": 3600,
                    "max_entries": 1000,
                    "default_expiration": 86400,
                },
            },
            "error_handling": {
                "max_retries": 3,
                "retry_delay": 1,
                "backoff_factor": 2,
            },
            "monitoring": {
                "enable_metrics": True,
                "metrics_interval": 60,
                "log_level": "INFO",
                "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        }

        # Load configuration from Hub if name provided
        if config_name:
            try:
                resource_manager = get_resource_manager()
                hub_config = resource_manager.load_config(
                    config_name,
                    version=config_version or "v1.0.0",
                )
                self.config = {**self.default_config, **hub_config}
            except Exception as e:
                raise ConfigError(f"Failed to load configuration: {e}")
        else:
            self.config = self.default_config.copy()

        # Update config with kwargs
        self.config.update(kwargs)

        # Get memory configuration
        memory_config = self.config.get("memory", {}).get("config", {})
        auto_cleanup = memory_config.get("auto_cleanup", True)
        cleanup_interval = memory_config.get("cleanup_interval", 3600)

        # Initialize base resource
        super().__init__(
            auto_cleanup=auto_cleanup,
            cleanup_interval=cleanup_interval,
        )

    async def _initialize(self) -> None:
        """Initialize agent resources."""
        # Initialize memory if enabled
        if self.config.get("memory", {}).get("enabled", True):
            memory_config = self.config.get("memory", {}).get("config", {})
            self.memory = SimpleMemory(**memory_config)
            await self.memory.initialize()

        # Initialize metrics collector if enabled
        if self.config.get("monitoring", {}).get("enable_metrics", True):
            # TODO: Initialize metrics collector
            pass

    async def _cleanup(self) -> None:
        """Clean up agent resources."""
        if hasattr(self, "memory"):
            await self.memory.cleanup()

    async def remember(self, key: str, value: Any) -> None:
        """Store a value in memory.

        Args:
            key: Key to store the value under
            value: Value to store
        """
        if hasattr(self, "memory"):
            await self.memory.store(key, value)

    async def recall(self, key: str) -> Any:
        """Retrieve a value from memory.

        Args:
            key: Key to retrieve the value for

        Returns:
            The stored value
        """
        if hasattr(self, "memory"):
            return await self.memory.retrieve(key)
        return None

    @abstractmethod
    async def process(self, input: str) -> str:
        """Process user input.

        Args:
            input: User input to process

        Returns:
            Processing result
        """
        pass

    @classmethod
    def from_hub(
        cls, config_name: str, config_version: str = "v1.0.0", **kwargs: Any
    ) -> "Agent":
        """Create agent instance from Hub configuration.

        Args:
            config_name: Name of the configuration to load
            config_version: Version of the configuration
            **kwargs: Additional configuration options

        Returns:
            Agent instance
        """
        return cls(
            config_name=config_name,
            config_version=config_version,
            **kwargs,
        )
