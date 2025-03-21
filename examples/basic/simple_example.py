"""Simple example of the PepperPy framework.

This example demonstrates the basic usage of PepperPy's core features including:
- Memory management
- Async operations
- Type safety
- Error handling
- Resource management

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    python simple_example.py
"""

import asyncio
from typing import List, Optional, cast

from pepperpy.core.logging import Logger
from pepperpy.core.memory import BaseMemory, MemoryManager
from pepperpy.core.types import Metadata

logger = Logger.get_logger(__name__)


class ConversationMemory(BaseMemory):
    """Memory item for conversations implementing PepperPy's BaseMemory."""

    def __init__(
        self,
        content: str,
        speaker: str,
        conversation_id: str,
        metadata: Optional[Metadata] = None,
    ) -> None:
        """Initialize the conversation memory.

        Args:
            content: The message content
            speaker: The speaker's identifier
            conversation_id: Unique conversation identifier
            metadata: Optional metadata dictionary
        """
        super().__init__(metadata=metadata)
        self.content = content
        self.speaker = speaker
        self.conversation_id = conversation_id


async def remember_conversation(
    memory_manager: MemoryManager,
    content: str,
    speaker: str,
    conversation_id: str,
    metadata: Optional[Metadata] = None,
) -> ConversationMemory:
    """Store a conversation message in memory.

    Args:
        memory_manager: The memory manager instance
        content: The message content
        speaker: The speaker's identifier
        conversation_id: Unique conversation identifier
        metadata: Optional metadata dictionary

    Returns:
        The stored memory item

    Raises:
        ValueError: If required parameters are missing
        RuntimeError: If memory storage fails
    """
    if not all([content, speaker, conversation_id]):
        raise ValueError("Missing required parameters")

    try:
        memory = ConversationMemory(
            content=content,
            speaker=speaker,
            conversation_id=conversation_id,
            metadata=metadata,
        )
        await memory_manager.store(memory)
        logger.debug(f"Stored memory for conversation {conversation_id}")
        return memory
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        raise RuntimeError(f"Memory storage failed: {e}") from e


async def recall_conversation(
    memory_manager: MemoryManager,
    conversation_id: str,
) -> List[ConversationMemory]:
    """Retrieve conversation history.

    Args:
        memory_manager: The memory manager instance
        conversation_id: Unique conversation identifier

    Returns:
        List of conversation memories ordered by timestamp

    Raises:
        ValueError: If conversation_id is missing
        RuntimeError: If memory retrieval fails
    """
    if not conversation_id:
        raise ValueError("conversation_id is required")

    try:
        memories = await memory_manager.get_by_filter(
            lambda x: isinstance(x, ConversationMemory)
            and x.conversation_id == conversation_id
        )
        return cast(
            List[ConversationMemory], sorted(memories, key=lambda x: x.created_at)
        )
    except Exception as e:
        logger.error(f"Failed to retrieve conversation: {e}")
        raise RuntimeError(f"Memory retrieval failed: {e}") from e


async def main() -> None:
    """Run the example demonstrating PepperPy's core features."""
    logger.info("Starting PepperPy Framework Example")

    async with MemoryManager() as memory_manager:
        try:
            conversation_id = "example_conversation"
            logger.info(f"Creating conversation with ID: {conversation_id}")

            # Store conversation memories
            logger.info("Storing conversation memories...")
            await remember_conversation(
                memory_manager=memory_manager,
                content="Hello, how can I help you?",
                speaker="assistant",
                conversation_id=conversation_id,
                metadata={"role": "system_greeting"},
            )

            await remember_conversation(
                memory_manager=memory_manager,
                content="I'd like to know more about PepperPy.",
                speaker="user",
                conversation_id=conversation_id,
                metadata={"intent": "information_request"},
            )

            await remember_conversation(
                memory_manager=memory_manager,
                content="PepperPy is a comprehensive framework for building AI applications.",
                speaker="assistant",
                conversation_id=conversation_id,
                metadata={"response_type": "definition"},
            )

            # Retrieve conversation history
            logger.info("Retrieving conversation history...")
            conversation = await recall_conversation(
                memory_manager=memory_manager,
                conversation_id=conversation_id,
            )

            print("\nConversation history:")
            for i, message in enumerate(conversation, 1):
                print(f"{i}. {message.speaker}: {message.content}")
                if message.metadata:
                    print(f"   Metadata: {message.metadata}")

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except RuntimeError as e:
            logger.error(f"Runtime error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
