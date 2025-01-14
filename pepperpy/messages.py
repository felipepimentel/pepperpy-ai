"""Message module."""

from dataclasses import dataclass
from typing import Any

from pepperpy.types import Message, MessageRole


@dataclass
class BaseMessage:
    """Base message class."""

    role: MessageRole
    content: str

    def to_dict(self) -> Message:
        """Convert message to dictionary.

        Returns:
            Message: Dictionary representation.
        """
        return {
            "role": self.role.value,
            "content": self.content,
        }


@dataclass
class UserMessage(BaseMessage):
    """User message class."""

    def __init__(self, content: str) -> None:
        """Initialize user message.

        Args:
            content: Message content.
        """
        super().__init__(role=MessageRole.USER, content=content)


@dataclass
class AssistantMessage(BaseMessage):
    """Assistant message class."""

    def __init__(self, content: str) -> None:
        """Initialize assistant message.

        Args:
            content: Message content.
        """
        super().__init__(role=MessageRole.ASSISTANT, content=content)


@dataclass
class SystemMessage(BaseMessage):
    """System message class."""

    def __init__(self, content: str) -> None:
        """Initialize system message.

        Args:
            content: Message content.
        """
        super().__init__(role=MessageRole.SYSTEM, content=content)


@dataclass
class FunctionMessage(BaseMessage):
    """Function message class."""

    name: str
    function_call: dict[str, Any] | None = None

    def __init__(self, content: str, name: str) -> None:
        """Initialize function message.

        Args:
            content: Message content.
            name: Function name.
        """
        super().__init__(role=MessageRole.FUNCTION, content=content)
        self.name = name

    def to_dict(self) -> Message:
        """Convert message to dictionary.

        Returns:
            Message: Dictionary representation.
        """
        message = super().to_dict()
        message["name"] = self.name
        if self.function_call:
            message["function_call"] = self.function_call
        return message
