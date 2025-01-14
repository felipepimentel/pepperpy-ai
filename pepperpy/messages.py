"""Messages module."""

from dataclasses import dataclass
from typing import Any, Literal, TypedDict, cast

from .types import Message, Role


class MessageDict(TypedDict, total=False):
    """Message dictionary."""

    role: Literal["user", "assistant", "system"]
    content: str
    name: str
    function_call: dict[str, Any]
    tool_calls: list[dict[str, Any]]


@dataclass
class MessageData:
    """Message data."""

    role: Role
    content: str
    name: str | None = None
    function_call: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None

    def to_dict(self) -> Message:
        """Convert to dictionary.

        Returns:
            Message dictionary.
        """
        message: MessageDict = {
            "role": cast(Literal["user", "assistant", "system"], self.role.value),
            "content": self.content,
        }
        if self.name is not None:
            message["name"] = self.name
        if self.function_call is not None:
            message["function_call"] = self.function_call
        if self.tool_calls is not None:
            message["tool_calls"] = self.tool_calls
        return cast(Message, message)

    @classmethod
    def from_dict(cls, data: Message) -> "MessageData":
        """Create from dictionary.

        Args:
            data: Message dictionary.

        Returns:
            Message data.
        """
        return cls(
            role=Role(data["role"]),
            content=data["content"],
            name=data.get("name"),
            function_call=data.get("function_call"),
            tool_calls=data.get("tool_calls"),
        )
