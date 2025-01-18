"""Base agent module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pepperpy.agents.types import AgentConfig, AgentResponse


class BaseAgent(ABC):
    """Base agent class."""

    def __init__(self, config: AgentConfig) -> None:
        """Initialize agent.

        Args:
            config: Agent configuration
        """
        self.config = config

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize agent resources."""
        pass

    @abstractmethod
    async def process(
        self, input_data: dict[str, Any], context: dict[str, Any] | None = None
    ) -> AgentResponse:
        """Process input data.

        Args:
            input_data: Input data to process
            context: Processing context

        Returns:
            Processed result with metadata
        """
        pass

    @abstractmethod
    def process_stream(
        self,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Process input data and stream results.

        Args:
            input_data: Input data to process
            context: Processing context

        Returns:
            Async iterator of processed chunks
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        pass

    @abstractmethod
    def validate_config(self) -> None:
        """Validate agent configuration."""
        pass

    def get_config(self) -> AgentConfig:
        """Get agent configuration.

        Returns:
            Agent configuration
        """
        return self.config
