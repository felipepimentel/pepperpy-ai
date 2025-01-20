"""API expert agent that makes API requests."""

import json
import re
from typing import Any, AsyncIterator, Dict, Optional

from pydantic import BaseModel, ConfigDict

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.llms.huggingface import HuggingFaceLLM
from pepperpy.tools.functions.api import APITool


class APIAgentConfig(BaseModel):
    """Configuration for API agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: HuggingFaceLLM
    api_tool: APITool
    api_docs: Optional[str] = None


class APIAgent(BaseAgent):
    """Agent that makes API requests based on natural language input."""

    def __init__(self, config: APIAgentConfig) -> None:
        """Initialize API agent.
        
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
            isinstance(config, APIAgentConfig)
            and isinstance(config.llm, HuggingFaceLLM)
            and isinstance(config.api_tool, APITool)
        )

    async def initialize(self) -> None:
        """Initialize the agent."""
        await self.config.llm.initialize()
        await self.config.api_tool.initialize()

    def extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text that may include markdown formatting.
        
        Args:
            text: Text that may contain JSON
            
        Returns:
            Extracted JSON object
            
        Raises:
            json.JSONDecodeError: If JSON cannot be parsed
        """
        # Try to extract JSON from markdown code block
        match = re.search(r"```(?:json)?\n(.*?)\n```", text, re.DOTALL)
        if match:
            text = match.group(1)
            
        # Clean up any remaining whitespace/newlines
        text = text.strip()
        
        return json.loads(text)

    async def process(self, input_text: str) -> str:
        """Process input and generate response.
        
        Args:
            input_text: Natural language request to process
            
        Returns:
            API response formatted as text
        """
        # First, convert natural language to API request details
        prompt = (
            "You are an expert in making API requests. "
            "Convert the following natural language request into a JSON object "
            "with the following fields:\n"
            "- method: HTTP method (GET, POST, etc)\n"
            "- url: Full URL for the request\n"
            "- headers: Optional request headers\n"
            "- params: Optional query parameters\n"
            "- json_data: Optional JSON body\n"
            "- data: Optional form data\n\n"
        )
        
        if self.config.api_docs:
            prompt += f"API Documentation:\n{self.config.api_docs}\n\n"
            
        prompt += f"Request: {input_text}\n\nJSON:"
        
        response = await self.config.llm.generate(prompt)
        
        try:
            request_details = self.extract_json(response.text)
        except json.JSONDecodeError:
            return "Error: Could not parse API request details"
            
        # Execute request
        result = await self.config.api_tool.execute(**request_details)
        
        if not result.success:
            return f"Error making API request: {result.error}"
            
        # Format response
        response_text = [
            f"Status: {result.data.status}",
            f"Time: {result.data.elapsed:.2f}s",
            "Response:",
            json.dumps(result.data.body, indent=2) if isinstance(result.data.body, (dict, list)) else result.data.body
        ]
            
        return "\n".join(response_text)

    async def process_stream(self, input_text: str) -> AsyncIterator[str]:
        """Process input and generate streaming response.
        
        Args:
            input_text: Natural language request to process
            
        Returns:
            API response chunks
        """
        # For now, we don't support streaming
        result = await self.process(input_text)
        yield result

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.config.llm.cleanup()
        await self.config.api_tool.cleanup() 