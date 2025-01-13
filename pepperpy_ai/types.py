"""Type definitions."""

from typing import Any, Union

# Type aliases for JSON values
JsonValue = Union[str, int, float, bool, None, list[Any], dict[str, Any]]
JsonDict = dict[str, str | int | float | bool | None | list[Any] | dict[str, Any]]

__all__ = ["JsonDict", "JsonValue"]


class Message:
    """Message type."""

    def __init__(
        self,
        content: str,
        role: str,
        metadata: JsonDict | None = None,
    ) -> None:
        """Initialize message.

        Args:
            content: Message content.
            role: Message role.
            metadata: Additional metadata.
        """
        self.content = content
        self.role = role
        self.metadata = metadata

    def to_dict(self) -> JsonDict:
        """Convert message to dictionary."""
        return {
            "content": self.content,
            "role": self.role,
            "metadata": self.metadata or {},
        }
