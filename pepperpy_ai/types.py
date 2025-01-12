"""Base types module."""

# Type aliases for JSON values
JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
type JsonDict = dict[str, JsonValue]

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
