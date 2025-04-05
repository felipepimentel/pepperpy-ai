"""
PepperPy Agent Memory.

Memory implementation for agent interactions.
"""

from pepperpy.agent.task import Memory, Message


class SimpleMemory(Memory):
    """Simple in-memory implementation of agent memory."""

    def __init__(self, max_messages: int = 100):
        """Initialize memory with optional message limit.

        Args:
            max_messages: Maximum number of messages to store
        """
        self.messages: list[Message] = []
        self.max_messages = max_messages
        self.metadata: dict[str, str] = {}

    async def add_message(self, message: Message) -> None:
        """Add a message to memory.

        Args:
            message: The message to add
        """
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            # Remove oldest message if over limit
            self.messages.pop(0)

    async def get_messages(self) -> list[Message]:
        """Get all messages from memory.

        Returns:
            List of messages
        """
        return self.messages

    async def clear(self) -> None:
        """Clear all messages from memory."""
        self.messages.clear()

    async def add_metadata(self, key: str, value: str) -> None:
        """Add metadata to memory.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    async def get_metadata(self, key: str) -> str | None:
        """Get metadata from memory.

        Args:
            key: Metadata key

        Returns:
            Metadata value or None if not found
        """
        return self.metadata.get(key)


class PersistentMemory(SimpleMemory):
    """Memory implementation that persists messages to storage."""

    def __init__(
        self, storage_path: str, max_messages: int = 100, auto_save: bool = True
    ):
        """Initialize persistent memory.

        Args:
            storage_path: Path to store messages
            max_messages: Maximum number of messages to keep in memory
            auto_save: Whether to automatically save on add
        """
        super().__init__(max_messages)
        self.storage_path = storage_path
        self.auto_save = auto_save

    async def add_message(self, message: Message) -> None:
        """Add a message and persist if auto_save is enabled.

        Args:
            message: The message to add
        """
        await super().add_message(message)
        if self.auto_save:
            await self.save()

    async def save(self) -> None:
        """Save messages to storage."""
        # Implementation would depend on storage mechanism
        # This is a placeholder for the actual implementation
        pass

    async def load(self) -> None:
        """Load messages from storage."""
        # Implementation would depend on storage mechanism
        # This is a placeholder for the actual implementation
        pass
