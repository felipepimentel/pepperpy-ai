"""Memory module example using PepperPy.

Purpose:
    Demonstrate how to use PepperPy's memory module for:
    - Storing conversation history
    - Retrieving conversation history
    - Managing memory items with different speakers
    - Recalling information based on conversation IDs

Requirements:
    - Python 3.8+
    - PepperPy framework
    - Asyncio support

Usage:
    1. Install dependencies:
       pip install -e .

    2. Run the example:
       python examples/memory/simple_memory.py
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional


class ConversationMemory:
    """Memory item for conversations.

    Attributes:
        content: The content of the memory
        speaker: The speaker identifier
        conversation_id: The conversation identifier
        metadata: Optional metadata for the memory
        timestamp: When the memory was created
    """

    def __init__(
        self,
        content: str,
        speaker: str,
        conversation_id: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize the conversation memory.

        Args:
            content: The content of the memory
            speaker: The speaker identifier
            conversation_id: The conversation identifier
            metadata: Optional metadata for the memory
        """
        self.content = content
        self.speaker = speaker
        self.conversation_id = conversation_id
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class MemoryManager:
    """Simple memory manager for demonstration purposes.

    Attributes:
        memories: List of stored memory items
    """

    def __init__(self) -> None:
        """Initialize the memory manager."""
        self.memories: List[ConversationMemory] = []

    async def store_memory(self, memory: ConversationMemory) -> None:
        """Store a memory item.

        Args:
            memory: The memory item to store
        """
        self.memories.append(memory)

    async def get_conversation_history(
        self,
        conversation_id: str,
    ) -> List[ConversationMemory]:
        """Get conversation history.

        Args:
            conversation_id: The conversation identifier

        Returns:
            List of conversation memories for the specified conversation
        """
        # Filter for the specified conversation ID
        conversation_memories = [
            memory
            for memory in self.memories
            if memory.conversation_id == conversation_id
        ]

        # Sort by timestamp (oldest first for conversation history)
        conversation_memories.sort(key=lambda x: x.timestamp)

        return conversation_memories


# Create a global memory manager
memory_manager = MemoryManager()


async def remember_conversation(
    content: str,
    speaker: str,
    conversation_id: str,
    metadata: Optional[Dict[str, str]] = None,
) -> ConversationMemory:
    """Remember a conversation message.

    Args:
        content: The content of the message
        speaker: The speaker identifier
        conversation_id: The conversation identifier
        metadata: Optional metadata for the memory

    Returns:
        The created conversation memory
    """
    memory = ConversationMemory(
        content=content,
        speaker=speaker,
        conversation_id=conversation_id,
        metadata=metadata,
    )
    await memory_manager.store_memory(memory)
    return memory


async def recall_conversation(
    conversation_id: str,
) -> List[ConversationMemory]:
    """Recall conversation history.

    Args:
        conversation_id: The conversation identifier

    Returns:
        List of conversation memories for the specified conversation
    """
    return await memory_manager.get_conversation_history(conversation_id)


async def main() -> None:
    """Run the memory module example."""
    try:
        print("PepperPy Memory Module Example")
        print("==============================")

        # Create a conversation
        conversation_id = "example_conversation"
        print(f"Creating conversation with ID: {conversation_id}")

        # Store some conversation memories
        print("\nStoring conversation memories...")
        await remember_conversation(
            content="Hello, how can I help you?",
            speaker="assistant",
            conversation_id=conversation_id,
        )

        await remember_conversation(
            content="I'd like to know more about PepperPy.",
            speaker="user",
            conversation_id=conversation_id,
        )

        await remember_conversation(
            content="PepperPy is a comprehensive framework for building AI applications.",
            speaker="assistant",
            conversation_id=conversation_id,
        )

        # Retrieve the conversation history
        print("\nRetrieving conversation history...")
        conversation = await recall_conversation(conversation_id)

        print("\nConversation history:")
        for i, message in enumerate(conversation):
            print(f"{i + 1}. {message.speaker}: {message.content}")

        # Create a second conversation
        second_conversation_id = "second_conversation"
        print(f"\nCreating a second conversation with ID: {second_conversation_id}")

        await remember_conversation(
            content="What features does PepperPy have?",
            speaker="user",
            conversation_id=second_conversation_id,
        )

        await remember_conversation(
            content="PepperPy provides modules for RAG, memory management, streaming, security, storage, and workflows.",
            speaker="assistant",
            conversation_id=second_conversation_id,
        )

        # Retrieve the second conversation history
        print("\nRetrieving second conversation history...")
        second_conversation = await recall_conversation(second_conversation_id)

        print("\nSecond conversation history:")
        for i, message in enumerate(second_conversation):
            print(f"{i + 1}. {message.speaker}: {message.content}")

        print(
            "\nThis demonstrates how the memory module can manage multiple conversations."
        )

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
