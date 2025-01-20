"""Base class for all agents."""

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Base class for all agents."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent's resources."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up any resources."""
        pass

    @abstractmethod
    async def process(self, *args, **kwargs):
        """Process input and generate output.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Agent-specific output
        """
        pass 