"""Base agent module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pepperpy.common.types import JSON


class BaseAgent(ABC):
    """Base agent class."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize agent.

        Args:
            config: Agent configuration
        """
        self.config = config

    @abstractmethod
    async def process(self, input_data: JSON, context: dict[str, Any]) -> str:
        """Process input data.

        Args:
            input_data: Input data to process
            context: Processing context

        Returns:
            Processed result
        """
        pass

    @abstractmethod
    async def process_stream(
        self, input_data: JSON, context: dict[str, Any]
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

    @abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Get agent configuration.

        Returns:
            Agent configuration
        """
        pass
