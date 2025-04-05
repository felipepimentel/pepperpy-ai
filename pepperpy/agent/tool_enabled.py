"""
PepperPy Tool-Enabled Agent Module.

Integration of tools with agents.
"""

from typing import Any

from pepperpy.agent.base import BaseAgentProvider
from pepperpy.agent.task import Message
from pepperpy.core.logging import get_logger
from pepperpy.tool.registry import get_tool, list_tools
from pepperpy.tool.result import ToolResult

logger = get_logger(__name__)


class ToolEnabledAgent(BaseAgentProvider):
    """Agent with tool capabilities."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize tool-enabled agent.

        Args:
            config: Optional configuration
        """
        super().__init__(config)
        self.enabled_tools: list[str] = self.config.get("enabled_tools", [])
        self.auto_tool_selection = self.config.get("auto_tool_selection", True)

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

    async def prepare_llm_response_with_tools(
        self, response: str, messages: list[Message]
    ) -> str:
        """Prepare LLM response with tool execution results.

        This method processes a response to extract tool calls,
        execute them, and update the response with results.

        Args:
            response: LLM response text
            messages: Message history

        Returns:
            Updated response with tool results
        """
        # This implementation would parse the response for tool calls
        # Execute the tools and include the results
        # For now, just return the original response
        return response

    def _extract_tool_calls(self, text: str) -> list[dict[str, Any]]:
        """Extract tool calls from text.

        Args:
            text: Text to extract tool calls from

        Returns:
            List of extracted tool calls
        """
        # Simplified implementation - would be more complex in practice
        # Could use regex or another parser to extract structured tool calls
        tool_calls = []

        # Return empty list for now
        return tool_calls
