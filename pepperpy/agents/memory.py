"""Memory implementations for the agents module."""

from typing import List

from pepperpy.agents.base import Memory, Message


class SimpleMemory(Memory):
    """Simple in-memory implementation of agent memory."""

    def __init__(self):
        """Initialize the memory."""
        self.messages: List[Message] = []

    async def add_message(self, message: Message) -> None:
        """Add a message to memory.
        
        Args:
            message: The message to add.
        """
        self.messages.append(message)

    async def get_messages(self) -> List[Message]:
        """Get all messages from memory.
        
        Returns:
            List of messages.
        """
        return self.messages.copy()

    async def clear(self) -> None:
        """Clear all messages from memory."""
        self.messages.clear() 