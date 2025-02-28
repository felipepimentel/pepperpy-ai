"""Core agent functionality for PepperPy."""

from typing import Any, Dict, List, Optional

from pepperpy.common.types import Message


class BaseAgent:
    """Base class for all PepperPy agents.

    This class defines the core functionality that all agents must implement.
    """

    def __init__(
        self,
        name: str,
        capabilities: List[str],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a base agent.

        Args:
            name: The name of the agent.
            capabilities: List of capabilities this agent has.
            config: Optional configuration for the agent.

        """
        self.name = name
        self.capabilities = capabilities
        self.config = config or {}

    async def analyze(
        self,
        query: str,
        depth: str = "comprehensive",
        style: str = "technical",
        **kwargs: Any,
    ) -> str:
        """Analyze a query and return insights.

        Args:
            query: The query to analyze.
            depth: The depth of analysis ("brief", "comprehensive", "detailed").
            style: The style of analysis ("technical", "academic", "casual").
            **kwargs: Additional keyword arguments.

        Returns:
            The analysis result as a string.

        """
        raise NotImplementedError("Subclasses must implement analyze()")

    async def write(
        self,
        topic: str,
        style: str = "technical",
        format: str = "report",
        tone: str = "neutral",
        length: str = "medium",
        **kwargs: Any,
    ) -> str:
        """Write content on a given topic.

        Args:
            topic: The topic to write about.
            style: The writing style ("technical", "academic", "casual").
            format: The output format ("report", "article", "summary").
            tone: The writing tone ("neutral", "formal", "informal").
            length: The desired length ("short", "medium", "long").
            **kwargs: Additional keyword arguments.

        Returns:
            The written content as a string.

        """
        raise NotImplementedError("Subclasses must implement write()")

    async def edit(
        self,
        content: str,
        focus: str = "clarity",
        style: str = "technical",
        **kwargs: Any,
    ) -> str:
        """Edit and improve content.

        Args:
            content: The content to edit.
            focus: The focus of editing ("clarity", "structure", "technical").
            style: The desired style ("technical", "academic", "casual").
            **kwargs: Additional keyword arguments.

        Returns:
            The edited content as a string.

        """
        raise NotImplementedError("Subclasses must implement edit()")

    async def process_message(
        self,
        message: Message,
        context: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Process a message and return a response.

        Args:
            message: The message to process.
            context: Optional context for processing.

        Returns:
            The response message.

        """
        raise NotImplementedError("Subclasses must implement process_message()")

    def has_capability(self, capability: str) -> bool:
        """Check if the agent has a specific capability.

        Args:
            capability: The capability to check for.

        Returns:
            True if the agent has the capability, False otherwise.

        """
        return capability in self.capabilities

    def validate_capabilities(self, required: List[str]) -> bool:
        """Validate that the agent has all required capabilities.

        Args:
            required: List of required capabilities.

        Returns:
            True if the agent has all required capabilities, False otherwise.

        """
        return all(self.has_capability(cap) for cap in required)

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: The configuration key.
            default: Default value if key doesn't exist.

        Returns:
            The configuration value or default.

        """
        return self.config.get(key, default)
