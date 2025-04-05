"""Assistant provider for agent tasks.

This module provides an assistant provider that can engage in conversations,
maintain context, and execute tasks using language models.
"""

from typing import Any, Dict, List, Optional, Union

from pepperpy.core.logging import get_logger
from pepperpy.llm import LLMProvider, Message, MessageRole
from pepperpy.plugin.plugin import PepperpyPlugin


class Assistant(PepperpyPlugin):
    """Assistant provider for agent tasks.

    This provider implements an AI assistant that can engage in conversations,
    maintain context, and execute tasks using language models.
    """

    name = "assistant"
    version = "0.1.0"
    description = "Assistant provider for agent tasks"
    author = "PepperPy Team"

    # Attributes auto-bound from plugin.yaml with default fallback values
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: str = "You are a helpful AI assistant."
    memory_size: int = 10
    llm: Optional[LLMProvider] = None
    logger = get_logger(__name__)

    def __init__(self) -> None:
        """Initialize the assistant."""
        super().__init__()
        self.messages: List[Message] = []
        self.context: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        """
        if self.initialized:
            return

        # Add system prompt
        self.messages = [Message(content=self.system_prompt, role=MessageRole.SYSTEM)]

        self.initialized = True
        self.logger.debug(f"Initialized with model={self.model}")

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        """
        self.messages = []
        self.context = {}

        self.initialized = False
        self.logger.debug("Resources cleaned up")

    async def chat(
        self,
        message: Union[str, Message],
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Send a message to the assistant and get a response.

        Args:
            message: Message to send
            context: Optional context to add to the conversation
            **kwargs: Additional arguments to pass to the LLM

        Returns:
            Assistant's response

        Raises:
            RuntimeError: If provider is not initialized or LLM is not set
        """
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        if not self.llm:
            raise RuntimeError("LLM provider not set")

        # Convert string to Message
        if isinstance(message, str):
            message = Message(content=message, role=MessageRole.USER)

        # Update context
        if context:
            self.context.update(context)

        # Add message to history
        self.messages.append(message)

        # Trim history if needed
        if len(self.messages) > self.memory_size + 1:  # +1 for system prompt
            self.messages = [self.messages[0]] + self.messages[-self.memory_size :]

        # Generate response using LLM
        response = await self.llm.generate(
            messages=self.messages,
            model=kwargs.get("model", self.model),
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )

        # Add response to history
        self.messages.append(
            Message(content=response.content, role=MessageRole.ASSISTANT)
        )

        return response.content
