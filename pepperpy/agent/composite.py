"""
PepperPy Composite Agent Module.

Composite pattern for building agents from multiple capabilities.
"""

from typing import Any, cast

from pepperpy.agent.base import BaseAgentProvider
from pepperpy.agent.capability import (
    BaseCapability,
    BaseMemoryAware,
    BaseToolUser,
)
from pepperpy.core.context import execution_context
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


class CompositeAgent(BaseAgentProvider):
    """Agent that is composed of multiple capabilities.

    Implements the composite pattern to allow an agent to be built
    from multiple independent capabilities.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize composite agent.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.capabilities: list[BaseCapability] = []
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the agent and all its capabilities."""
        if self.initialized:
            return

        # Initialize each capability
        for capability in self.capabilities:
            await capability.initialize()

        self.initialized = True
        logger.debug(
            f"Initialized composite agent with {len(self.capabilities)} capabilities"
        )

    async def cleanup(self) -> None:
        """Clean up the agent and its capabilities."""
        if not self.initialized:
            return

        # Clean up each capability in reverse order
        for capability in reversed(self.capabilities):
            await capability.cleanup()

        self.initialized = False
        logger.debug("Cleaned up composite agent")

    def add_capability(self, capability: BaseCapability) -> "CompositeAgent":
        """Add a capability to the agent.

        Args:
            capability: Capability to add

        Returns:
            Self for method chaining
        """
        self.capabilities.append(capability)
        return self

    def has_capability(self, capability_type: type) -> bool:
        """Check if the agent has a capability of the specified type.

        Args:
            capability_type: Capability type to check for

        Returns:
            True if the agent has the capability, False otherwise
        """
        return any(isinstance(cap, capability_type) for cap in self.capabilities)

    def get_capability(self, capability_type: type) -> BaseCapability | None:
        """Get a capability of the specified type.

        Args:
            capability_type: Capability type to get

        Returns:
            Capability instance or None if not found
        """
        for cap in self.capabilities:
            if isinstance(cap, capability_type):
                return cap
        return None

    async def process_message(
        self, message: str, context: dict[str, Any] | None = None
    ) -> str:
        """Process a message using the agent's capabilities.

        This implementation delegates to specific capabilities based on the message.

        Args:
            message: Message to process
            context: Optional context data

        Returns:
            Agent response
        """
        if not self.initialized:
            await self.initialize()

        ctx = context or {}

        # Create execution context
        async with execution_context() as exec_ctx:
            exec_ctx.add_metadata("agent_type", "composite")

            # Check if the agent has tool capabilities
            if self.has_capability(BaseToolUser):
                # Get the tool user capability
                tool_user = cast(BaseToolUser, self.get_capability(BaseToolUser))

                # Get available tools and add to context
                tools = await tool_user.get_available_tools()
                exec_ctx.add_metadata("available_tools", [t["name"] for t in tools])

                # Here we would extract tool calls from the message and execute them
                # This is a simplified implementation

            # Check if the agent has memory capabilities
            if self.has_capability(BaseMemoryAware):
                # Get the memory capability
                memory = cast(BaseMemoryAware, self.get_capability(BaseMemoryAware))

                # Retrieve relevant context from memory
                memory_items = await memory.retrieve_from_memory(message)
                if memory_items:
                    exec_ctx.add_metadata("memory_items", len(memory_items))

                    # Here we would use memory items to enhance the response
                    # This is a simplified implementation

                # Add the message to memory
                await memory.add_to_memory(message)

            # Process message with base implementation
            response = f"Processed message: {message}"

            return response


class CompositeAgentBuilder:
    """Builder for creating composite agents.

    Provides a fluent API for adding capabilities to an agent.
    """

    def __init__(self) -> None:
        """Initialize the builder."""
        self.agent = CompositeAgent()

    def with_tool_capability(
        self, enabled_tools: list[str] | None = None
    ) -> "CompositeAgentBuilder":
        """Add tool user capability to the agent.

        Args:
            enabled_tools: Optional list of enabled tool names

        Returns:
            Builder for method chaining
        """
        config = {}
        if enabled_tools:
            config["enabled_tools"] = enabled_tools

        self.agent.add_capability(BaseToolUser(config))
        return self

    def with_memory_capability(
        self, memory_type: str = "simple"
    ) -> "CompositeAgentBuilder":
        """Add memory capability to the agent.

        Args:
            memory_type: Type of memory to use

        Returns:
            Builder for method chaining
        """
        config = {"memory_type": memory_type}
        self.agent.add_capability(BaseMemoryAware(config))
        return self

    def with_custom_capability(
        self, capability: BaseCapability
    ) -> "CompositeAgentBuilder":
        """Add a custom capability to the agent.

        Args:
            capability: Capability to add

        Returns:
            Builder for method chaining
        """
        self.agent.add_capability(capability)
        return self

    def build(self) -> CompositeAgent:
        """Build the composite agent.

        Returns:
            Configured composite agent
        """
        return self.agent


def create_composite_agent(**config: Any) -> CompositeAgent:
    """Create a composite agent with the given configuration.

    Args:
        **config: Configuration parameters

    Returns:
        Configured composite agent
    """
    builder = CompositeAgentBuilder()

    # Add tool capability if enabled
    if config.get("enable_tools", True):
        builder.with_tool_capability(config.get("enabled_tools"))

    # Add memory capability if enabled
    if config.get("enable_memory", True):
        builder.with_memory_capability(config.get("memory_type", "simple"))

    # Return built agent
    return builder.build()
