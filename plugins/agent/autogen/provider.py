"""AutoGen provider implementation for the agent module."""

import logging
import re
from typing import dict, list, Optional, Any

from pepperpy.agent.base import AgentError, BaseAgentProvider, Message
from pepperpy.agent import AgentProvider
from pepperpy.agent.base import AgentError


class ServiceMixin:
    """Mixin to provide access to framework services."""

    def __init__(self):
        """Initialize the service mixin."""
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._framework = None

    def _get_framework(self):
        """Get the PepperPy framework instance.

        Returns:
            PepperPy framework instance or None if not available
        """
        # We don't actually need to get the framework instance directly
        # Just return None, and the individual service methods will handle
        # getting their services directly
        return None

    def llm(self):
        """Get the LLM provider from the framework.

        Returns:
            LLM provider instance or None if not available
        """
        try:
            # Get the LLM directly from the registry
            from pepperpy.llm.registry import get_provider

            return get_provider()
        except Exception as e:
            self.logger.warning(f"LLM provider not available: {e}")
            return None

    def memory(self):
        """Get the memory provider from the framework.

        Returns:
            Memory provider instance or None if not available
        """
        try:
            # Get the memory directly from the registry
            from pepperpy.memory.registry import get_provider

            return get_provider()
        except Exception as e:
            self.logger.warning(f"Memory provider not available: {e}")
            return None

    def get_tool(self, tool_name: str):
        """Get a tool provider by name.

        Args:
            tool_name: Name of the tool to get

        Returns:
            Tool provider instance or None if not available
        """
        try:
            from pepperpy.tool.registry import get_tool

            return get_tool(tool_name)
        except Exception as e:
            self.logger.warning(f"Tool {tool_name} not available: {e}")
            return None


class AutoGenAgent(class AutoGenAgent(BaseAgentProvider, ServiceMixin):
    """AutoGen implementation of an agent."""):
    """
    Agent autogenagent provider.
    
    This provider implements autogenagent functionality for the PepperPy agent framework.
    """

    def __init__(self, **kwargs: Any):
        """Initialize the agent with configuration.

        Args:
            **kwargs: Configuration parameters
        """
        BaseAgentProvider.__init__(self, **kwargs)
        ServiceMixin.__init__(self)

    async def _initialize_resources(self) -> None:
 """Initialize resources for the agent.
 """
        self.logger.debug(
            f"Initialized with model={self.model}"
        )

    async def _cleanup_resources(self) -> None:
 """Clean up resources for the agent.
 """
        # No specific cleanup needed for basic agent
        pass

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
        try:
            # Get LLM provider through the framework
            llm_provider = self.llm()
            if not llm_provider:
                raise AgentError("LLM provider not available")

            # Process message with LLM
            response = await llm_provider.completion(message)

            # Process tools if auto tool selection is enabled
            if self.auto_tool_selection and context and "messages" in context:
                messages = [
                    Message(**msg) if isinstance(msg, dict) else msg
                    for msg in context.get("messages", [])
                ]
                response = await self.prepare_response_with_tools(
                    str(response), messages
                )

            return str(response)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            raise AgentError(f"Failed to process message: {e}") from e

    def _extract_tool_calls(self, text: str) -> list[dict[str, Any]]:
        """Extract tool calls from text.

        Args:
            text: Text to extract tool calls from

        Returns:
            list of extracted tool calls
        """
        tool_calls = []

        # Simple extraction based on specific format
        # Example: "Tool: tool_name(param1=value1, param2=value2)"
        pattern = r"Tool:\s+(\w+)(?:\(([^)]*)\))?"
        matches = re.finditer(pattern, text)

        for match in matches:
            tool_name = match.group(1)
            params_str = match.group(2) or ""

            # Parse parameters
            parameters = {}
            if params_str:
                param_pairs = params_str.split(",")
                for pair in param_pairs:
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        parameters[key.strip()] = value.strip().strip("\"'")

            tool_calls.append({"name": tool_name, "parameters": parameters})

        return tool_calls

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task based on input data.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result
        """
        # Get task type from input
        task_type = input_data.get("task")

        if not task_type:
            raise AgentError("No task specified")

        try:
            # Handle different task types
            if task_type == "chat":
                # Handle chat task with message history
                messages = input_data.get("messages", [])
                if not messages:
                    # Add system message if not present
                    system_prompt = self.config.get(
                        "system_prompt", "You are a helpful assistant."
                    )
                    messages.append({"role": "system", "content": system_prompt})

                    # Add user message from task if available
                    if "content" in input_data:
                        messages.append(
                            {"role": "user", "content": input_data["content"]}
                        )

                # Get the last user message to process
                last_user_message = None
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        last_user_message = msg.get("content")
                        break

                if not last_user_message:
                    raise AgentError("No user message found")

                # Process the message with context
                context = {"messages": messages}
                response = await self.process_message(last_user_message, context)

                return {
                    "status": "success",
                    "response": response,
                    "messages": messages + [{"role": "assistant", "content": response}],
                }
            else:
                # Treat task as a direct query/prompt
                response = await self.process_message(task_type)

                return {"status": "success", "content": response}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "message": str(e)}

    async def initialize(self, config: dict[str, Any]) -> bool:
        """
        Initialize the provider with the given configuration.
        
        Args:
            config: Configuration parameters
            
        Returns:
            True if initialization was successful, False otherwise
        """
        self.config = config
        return True

    async def cleanup(self) -> bool:
        """
        Clean up resources used by the provider.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        return True