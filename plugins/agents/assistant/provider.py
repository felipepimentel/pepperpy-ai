"""Assistant Interfaces.

This module defines the core interfaces for the assistant domain,
including message formats, context management, and base classes.
"""

from typing import Any, Dict, Optional

from pepperpy.core import BaseProvider


class Message:
    """Standard message format for assistant communication.

    Args:
        content: Message content
        metadata: Optional message metadata

    Example:
        >>> message = Message("Hello!", metadata={"type": "greeting"})
        >>> print(message.content)
        'Hello!'
    """

    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.content = content
        self.metadata = metadata or {}


class Context:
    """Assistant execution context.

    Args:
        assistant_id: Unique assistant identifier
        metadata: Optional context metadata

    Example:
        >>> context = Context("assistant_1", metadata={"mode": "chat"})
        >>> print(context.assistant_id)
        'assistant_1'
    """

    def __init__(
        self,
        assistant_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.assistant_id = assistant_id
        self.metadata = metadata or {}


class Assistant(BaseProvider):
    """Base assistant implementation.

    This class defines the common interface for all assistants.
    It provides basic message processing and context management.

    Args:
        name: Assistant name
        **kwargs: Assistant-specific configuration

    Example:
        >>> assistant = Assistant("helper")
        >>> response = assistant.process_message("Hello!")
        >>> print(response.content)
    """

    

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    model: str = "default-model"
    base_url: str
    temperature: float = 0.7
    max_tokens: int = 1024
    user_id: str
    client: Optional[Any]

    def __init__(
        self,
        name: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(name, **kwargs)
        self.provider_type = "assistant"

    def process_message(
        self,
        content: str,
        context: Optional[Context] = None,
    ) -> Message:
        """Process an incoming message.

        Args:
            content: Message content
            context: Optional processing context

        Returns:
            Response message

        Example:
            >>> assistant = Assistant("helper")
            >>> response = assistant.process_message("Hello!")
            >>> print(response.content)
        """
        # Base implementation just echoes the message
        return Message(f"Echo: {content}")

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            Assistant name and type
        """
        return f"{self.name} ({self.provider_type})"
