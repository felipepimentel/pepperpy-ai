"""Simple example of the PepperPy framework.

Purpose:
    Demonstrate the basic structure and capabilities of the PepperPy framework.

Requirements:
    - Python 3.8+
    - Asyncio support

Usage:
    python simple_example.py
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional


class ConversationMemory:
    """Memory item for conversations."""

    def __init__(
        self,
        content: str,
        speaker: str,
        conversation_id: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize the conversation memory."""
        self.content = content
        self.speaker = speaker
        self.conversation_id = conversation_id
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class MemoryManager:
    """Simple memory manager for demonstration purposes."""

    def __init__(self) -> None:
        """Initialize the memory manager."""
        self.memories: List[ConversationMemory] = []

    async def store_memory(self, memory: ConversationMemory) -> None:
        """Store a memory item."""
        self.memories.append(memory)

    async def get_conversation_history(
        self,
        conversation_id: str,
    ) -> List[ConversationMemory]:
        """Get conversation history."""
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
    """Remember a conversation message."""
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
    """Recall conversation history."""
    return await memory_manager.get_conversation_history(conversation_id)


async def main() -> None:
    """Run the example."""
    try:
        print("PepperPy Framework Example")
        print("=========================")
        print("\nPepperPy provides modules for:")
        print("- RAG (Retrieval Augmented Generation)")
        print("- Memory Management")
        print("- Streaming")
        print("- Security")
        print("- Storage")
        print("- Workflows")
        print("\nThis is a simplified demonstration of the framework.")

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

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
