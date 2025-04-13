"""
PepperPy Agent Base Module.

Base classes and interfaces for agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from pepperpy.core.base import PepperpyError
from pepperpy.core.logging import get_logger
from pepperpy.plugin import PepperpyPlugin
from pepperpy.tool.registry import get_tool, list_tools
from pepperpy.tool.result import ToolResult

logger = get_logger(__name__)


class AgentError(PepperpyError):
    """Base error for agent operations."""

    pass


class Message:
    """Message in a conversation."""

    def __init__(
        self,
        role: str,
        content: str,
        name: str | None = None,
        function_call: dict[str, Any] | None = None,
    ) -> None:
        """Initialize message.

        Args:
            role: Message role (system, user, assistant, function)
            content: Message content
            name: Optional name for function messages
            function_call: Optional function call details
        """
        self.role = role
        self.content = content
        self.name = name
        self.function_call = function_call

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        result: dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }
        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        return result


@runtime_checkable
class AgentProvider(Protocol):
    """Protocol defining agent provider interface."""

    async def initialize(self) -> None:
        """Initialize agent provider resources."""
        ...

    async def cleanup(self) -> None:
        """Clean up agent provider resources."""
        ...

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """Get available tools in a format suitable for LLM context.

        Returns:
            List of tool metadata for LLM
        """
        ...

    async def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions for LLM context.

        Returns:
            Formatted string with tool descriptions
        """
        ...

    async def execute_tool(
        self, tool_name: str, command: str | None = None, **parameters: Any
    ) -> ToolResult:
        """Execute a tool.

        Args:
            tool_name: Name of the tool
            command: Command to execute (optional)
            **parameters: Tool parameters

        Returns:
            Tool execution result
        """
        ...

    async def prepare_response_with_tools(
        self, response: str, messages: list[Message]
    ) -> str:
        """Prepare agent response with tool execution results.

        Args:
            response: Agent response text
            messages: Message history

        Returns:
            Updated response with tool results
        """
        ...


class BaseAgentProvider(PepperpyPlugin, ABC):
    """Base class for agent providers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize agent provider.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        self.config = config or {}
        self.enabled_tools: list[str] = self.config.get("enabled_tools", [])
        self.auto_tool_selection = self.config.get("auto_tool_selection", True)
        self.initialized = False

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """Get available tools in a format suitable for LLM context.

        Returns:
            List of tool metadata for LLM
        """
        all_tools = list_tools()

        # If enabled_tools is defined, filter to only those tools
        if self.enabled_tools:
            return [tool for tool in all_tools if tool["name"] in self.enabled_tools]

        return all_tools

    async def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions for LLM context.

        Returns:
            Formatted string with tool descriptions
        """
        tools = await self.get_available_tools()

        if not tools:
            return "No tools available."

        descriptions = []
        for tool in tools:
            required_params = []
            optional_params = []

            if "parameters_schema" in tool:
                schema = tool["parameters_schema"]
                if "properties" in schema:
                    for name, param in schema["properties"].items():
                        param_desc = (
                            f"{name}: {param.get('description', 'No description')}"
                        )
                        if "required" in schema and name in schema["required"]:
                            required_params.append(param_desc)
                        else:
                            optional_params.append(param_desc)

            required_str = ""
            if required_params:
                required_str = "\nRequired parameters:\n- " + "\n- ".join(
                    required_params
                )

            optional_str = ""
            if optional_params:
                optional_str = "\nOptional parameters:\n- " + "\n- ".join(
                    optional_params
                )

            descriptions.append(
                f"Tool: {tool['name']}\n"
                f"Description: {tool.get('description', 'No description')}\n"
                f"Category: {tool.get('category', 'other')}"
                f"{required_str}{optional_str}\n"
            )

        return "\n\n".join(descriptions)

    async def execute_tool(
        self, tool_name: str, command: str | None = None, **parameters: Any
    ) -> ToolResult:
        """Execute a tool.

        Args:
            tool_name: Name of the tool
            command: Command to execute (optional)
            **parameters: Tool parameters

        Returns:
            Tool execution result
        """
        # Get the tool
        tool = get_tool(tool_name)
        if not tool:
            logger.warning(f"Tool not found: {tool_name}")
            return ToolResult(
                success=False, data={}, error=f"Tool not found: {tool_name}"
            )

        # Initialize if needed
        if not tool.initialized:
            try:
                await tool.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize tool {tool_name}: {e}")
                return ToolResult(
                    success=False, data={}, error=f"Failed to initialize tool: {e!s}"
                )

        # Execute the tool
        try:
            logger.debug(
                f"Executing tool {tool_name}"
                + (f" command {command}" if command else "")
            )

            # If command is provided, use the execute method
            if command:
                result_dict = await tool.execute(command, **parameters)
                return ToolResult.from_dict(result_dict)

            # Otherwise, try to determine the command from capabilities
            capabilities = await tool.get_capabilities()
            if not capabilities:
                return ToolResult(
                    success=False,
                    data={},
                    error=f"Tool {tool_name} has no capabilities",
                )

            # Use the first capability as default command
            result_dict = await tool.execute(capabilities[0], **parameters)
            return ToolResult.from_dict(result_dict)

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return ToolResult(
                success=False, data={}, error=f"Tool execution error: {e!s}"
            )

    async def prepare_response_with_tools(
        self, response: str, messages: list[Message]
    ) -> str:
        """Prepare agent response with tool execution results.

        This method processes a response to extract tool calls,
        execute them, and update the response with results.

        Args:
            response: Agent response text
            messages: Message history

        Returns:
            Updated response with tool results
        """
        # Extract and execute tool calls
        tool_calls = self._extract_tool_calls(response)

        if not tool_calls:
            return response

        # Execute tools and gather results
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            command = tool_call.get("command")
            parameters = tool_call.get("parameters", {})

            if tool_name:
                result = await self.execute_tool(tool_name, command, **parameters)
                results.append({"tool": tool_name, "result": result.to_dict()})

        # Update response with results
        updated_response = response
        for result in results:
            # Add result after tool call
            tool_marker = f"Tool: {result['tool']}"
            if tool_marker in updated_response:
                result_text = f"\nResult: {result['result']}"
                updated_response = updated_response.replace(
                    tool_marker, f"{tool_marker}{result_text}"
                )

        return updated_response

    def _extract_tool_calls(self, text: str) -> list[dict[str, Any]]:
        """Extract tool calls from text.

        Args:
            text: Text to extract tool calls from

        Returns:
            List of extracted tool calls
        """
        # Implement tool call extraction logic
        # This could use regex or another parser to extract structured tool calls
        tool_calls = []
        return tool_calls

    async def initialize(self) -> None:
        """Initialize agent resources."""
        if self.initialized:
            return
        await self._initialize_resources()
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        if not self.initialized:
            return
        await self._cleanup_resources()
        self.initialized = False

    async def _initialize_resources(self) -> None:
        """Initialize resources for the agent.

        This method should be overridden by subclasses to
        initialize specific resources.
        """
        pass

    async def _cleanup_resources(self) -> None:
        """Clean up resources for the agent.

        This method should be overridden by subclasses to
        clean up specific resources.
        """
        pass

    @abstractmethod
    async def process_message(
        self, message: str, context: dict[str, Any] | None = None
    ) -> str:
        """Process a message and return a response.

        Args:
            message: Input message
            context: Optional context dictionary

        Returns:
            Agent response

        Raises:
            AgentError: If message processing fails
        """
        pass
