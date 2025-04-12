"""
PepperPy Agent Capability Module.

Defines the capability protocols for agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Capability(Protocol):
    """Base protocol for agent capabilities.

    Capabilities are composable units of functionality that can be added to agents.
    """

    async def initialize(self) -> None:
        """Initialize the capability."""
        ...

    async def cleanup(self) -> None:
        """Clean up the capability."""
        ...

    async def get_description(self) -> str:
        """Get a description of this capability for agent context.

        Returns:
            Description of the capability
        """
        ...


class BaseCapability(ABC):
    """Base implementation for capabilities.

    Provides common functionality and ensures protocol conformance.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the capability.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the capability."""
        if self.initialized:
            return
        self.initialized = True

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the capability."""
        if not self.initialized:
            return
        self.initialized = False

    @abstractmethod
    async def get_description(self) -> str:
        """Get a description of this capability for agent context.

        Returns:
            Description of the capability
        """
        pass


@runtime_checkable
class ToolUser(Capability, Protocol):
    """Protocol for agents that can use tools."""

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """Get available tools for this agent.

        Returns:
            List of tool metadata
        """
        ...

    async def execute_tool(self, tool_name: str, **parameters: Any) -> dict[str, Any]:
        """Execute a tool.

        Args:
            tool_name: Name of the tool to execute
            **parameters: Tool parameters

        Returns:
            Tool execution result
        """
        ...


class BaseToolUser(BaseCapability):
    """Base implementation of the ToolUser capability."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the tool user capability.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.enabled_tools = self.config.get("enabled_tools", [])

    async def initialize(self) -> None:
        """Initialize tool user capability."""
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up tool user capability."""
        await super().cleanup()

    async def get_description(self) -> str:
        """Get tool user capability description.

        Returns:
            Description of the capability
        """
        return "Can use tools to perform actions."

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """Get available tools for this agent.

        Returns:
            List of tool metadata
        """
        from pepperpy.tool.registry import list_tools

        all_tools = list_tools()

        # Filter to enabled tools if specified
        if self.enabled_tools:
            return [tool for tool in all_tools if tool["name"] in self.enabled_tools]

        return all_tools

    async def execute_tool(self, tool_name: str, **parameters: Any) -> dict[str, Any]:
        """Execute a tool.

        Args:
            tool_name: Name of the tool to execute
            **parameters: Tool parameters

        Returns:
            Tool execution result
        """
        from pepperpy.tool.registry import get_tool
        from pepperpy.tool.result import ToolResult

        # Get the tool
        tool = get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False, data={}, error=f"Tool not found: {tool_name}"
            ).to_dict()

        # Initialize if needed
        if not tool.initialized:
            try:
                await tool.initialize()
            except Exception as e:
                return ToolResult(
                    success=False, data={}, error=f"Failed to initialize tool: {e!s}"
                ).to_dict()

        # Execute the tool
        try:
            capabilities = await tool.get_capabilities()
            if not capabilities:
                return ToolResult(
                    success=False,
                    data={},
                    error=f"Tool {tool_name} has no capabilities",
                ).to_dict()

            # Use the first capability as default command
            result_dict = await tool.execute(capabilities[0], **parameters)
            return result_dict

        except Exception as e:
            return ToolResult(
                success=False, data={}, error=f"Tool execution error: {e!s}"
            ).to_dict()


@runtime_checkable
class MemoryAware(Capability, Protocol):
    """Protocol for agents with memory capability."""

    async def add_to_memory(
        self, content: Any, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add content to memory.

        Args:
            content: Content to add to memory
            metadata: Optional metadata about the content
        """
        ...

    async def retrieve_from_memory(
        self, query: str, limit: int = 5
    ) -> list[tuple[Any, float]]:
        """Retrieve content from memory based on query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of (content, relevance_score) tuples
        """
        ...


class BaseMemoryAware(BaseCapability):
    """Base implementation of the MemoryAware capability."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the memory capability.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.memory_store = None

    async def initialize(self) -> None:
        """Initialize memory capability."""
        await super().initialize()

        # Initialize memory store here
        # This is just a placeholder, actual implementation would
        # create a specific type of memory store based on config

    async def cleanup(self) -> None:
        """Clean up memory capability."""
        # Clean up memory store
        self.memory_store = None
        await super().cleanup()

    async def get_description(self) -> str:
        """Get memory capability description.

        Returns:
            Description of the capability
        """
        return "Can remember and recall information from previous interactions."

    async def add_to_memory(
        self, content: Any, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add content to memory.

        Args:
            content: Content to add to memory
            metadata: Optional metadata about the content
        """
        # Placeholder - actual implementation would depend on memory store
        pass

    async def retrieve_from_memory(
        self, query: str, limit: int = 5
    ) -> list[tuple[Any, float]]:
        """Retrieve content from memory based on query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of (content, relevance_score) tuples
        """
        # Placeholder - actual implementation would depend on memory store
        return []
