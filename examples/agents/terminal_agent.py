"""Terminal expert agent that executes commands."""

import asyncio
from typing import Any, AsyncIterator

from pydantic import BaseModel, ConfigDict

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.llms.huggingface import HuggingFaceLLM
from pepperpy.tools.functions.terminal import TerminalTool


class TerminalAgentConfig(BaseModel):
    """Configuration for terminal agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: HuggingFaceLLM
    terminal_tool: TerminalTool


class TerminalAgent(BaseAgent):
    """Agent that executes terminal commands based on natural language input."""

    def __init__(self, config: TerminalAgentConfig) -> None:
        """Initialize terminal agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config

    @classmethod
    def validate_config(cls, config: Any) -> bool:
        """Validate agent configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        return (
            isinstance(config, TerminalAgentConfig)
            and isinstance(config.llm, HuggingFaceLLM)
            and isinstance(config.terminal_tool, TerminalTool)
        )

    async def initialize(self) -> None:
        """Initialize the agent."""
        await self.config.llm.initialize()
        await self.config.terminal_tool.initialize()

    async def process(self, input_text: str) -> str:
        """Process input and generate response.
        
        Args:
            input_text: Natural language command to process
            
        Returns:
            Command execution result
        """
        # First, convert natural language to terminal command
        prompt = (
            "You are an expert in Unix/Linux terminal commands. "
            "Convert the following natural language request into the most appropriate "
            "terminal command. Return ONLY the command, nothing else:\n\n"
            f"{input_text}"
        )
        
        response = await self.config.llm.generate(prompt)
        command = response.text.strip()
        
        # Execute command
        result = await self.config.terminal_tool.execute(command=command)
        
        if not result.success:
            return f"Error executing command: {result.error}"
            
        # Format output
        output = []
        if result.data.stdout:
            output.append(result.data.stdout)
        if result.data.stderr:
            output.append(f"Errors: {result.data.stderr}")
            
        return "\n".join(output) if output else "Command executed successfully"

    async def process_stream(self, input_text: str) -> AsyncIterator[str]:
        """Process input and generate streaming response.
        
        Args:
            input_text: Natural language command to process
            
        Returns:
            Command execution result chunks
        """
        # For now, we don't support streaming
        result = await self.process(input_text)
        yield result

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.config.llm.cleanup()
        await self.config.terminal_tool.cleanup() 