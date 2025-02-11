"""Research Assistant Agent.

This module provides a research assistant agent that helps with academic research.
"""

from typing import Any, Dict
from uuid import uuid4

from pepperpy.agents.base import BaseAgent
from pepperpy.core.types import Message, MessageType
from pepperpy.monitoring import logger


class ResearchAssistant(BaseAgent):
    """Research assistant agent that helps with academic research."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the research assistant.

        Args:
        ----
            config: Agent configuration loaded from .pepper_hub

        """
        super().__init__(config)
        self.log = logger.bind(agent="research_assistant")

    async def run(self, topic: str) -> str:
        """Run the research assistant with a given topic.

        Args:
        ----
            topic: The research topic to analyze

        Returns:
        -------
            The agent's response analyzing the topic

        """
        self.log.info("Running research assistant", topic=topic)

        # Get the model configuration
        model_config = self.config.get("model", {})
        provider = model_config.get("provider", "openrouter")
        model = model_config.get("name", "openai/gpt-4-turbo-preview")

        # Get the prompts
        system_prompt = self._get_prompt("system")
        user_prompt = self._get_prompt("user").format(topic=topic)

        # Create properly typed messages
        messages = [
            Message(
                id=str(uuid4()),
                type=MessageType.COMMAND,
                content={"text": system_prompt},
            ),
            Message(
                id=str(uuid4()), type=MessageType.QUERY, content={"text": user_prompt}
            ),
        ]

        # Run the model
        response = await self.run_model(
            provider=provider,
            model=model,
            messages=messages,
        )

        return response

    def _get_prompt(self, name: str) -> str:
        """Get a prompt by name from the configuration.

        Args:
        ----
            name: Name of the prompt to get

        Returns:
        -------
            The prompt content

        Raises:
        ------
            ValueError: If the prompt is not found

        """
        for prompt in self.config.get("prompts", []):
            if prompt.get("name") == name:
                return prompt.get("content", "")
        raise ValueError(f"Prompt '{name}' not found in configuration")
