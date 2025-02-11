"""Base agent class for Pepperpy agents.

This module provides the base class for all Pepperpy agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pepperpy.monitoring import logger
from pepperpy.providers import get_provider
from pepperpy.providers.openai import Message


class BaseAgent(ABC):
    """Base class for all Pepperpy agents."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the base agent.

        Args:
        ----
            config: Agent configuration loaded from .pepper_hub

        """
        self.config = config
        self._logger = logger.bind(agent=self.__class__.__name__)

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Run the agent with the given parameters.

        Args:
        ----
            **kwargs: Parameters for the agent run

        Returns:
        -------
            The agent's response

        """
        raise NotImplementedError

    async def run_model(
        self,
        provider: str,
        model: str,
        messages: List[Message],
        **kwargs: Any,
    ) -> str:
        """Run a model with the given parameters.

        Args:
        ----
            provider: The provider to use (e.g., openai, anthropic)
            model: The model to use
            messages: The messages to send to the model
            **kwargs: Additional parameters for the model

        Returns:
        -------
            The model's response

        """
        self._logger.info(
            "Running model",
            provider=provider,
            model=model,
            num_messages=len(messages),
        )

        provider_instance = get_provider(provider)
        try:
            await provider_instance.initialize()
            response = await provider_instance.chat_completion(
                model=model,
                messages=messages,
                **kwargs,
            )
            return response
        finally:
            await provider_instance.cleanup()
