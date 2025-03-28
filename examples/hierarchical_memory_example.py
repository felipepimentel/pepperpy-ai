"""
Example demonstrating the use of hierarchical memory in an agent.

This example shows how to set up and use a hierarchical memory system
with working, episodic, semantic, and procedural memory.
"""

import asyncio
import json
import os
from pathlib import Path

from pepperpy.agents.base import Message
from pepperpy.agents.hierarchical_memory import (
    HierarchicalMemory,
    MemoryManager,
)


# Function wrapper to make it JSON serializable
class SerializableFunction:
    """Wrapper for functions to make them JSON serializable."""

    def __init__(self, func):
        self.func = func
        self.name = func.__name__ if hasattr(func, "__name__") else "lambda"

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def to_dict(self):
        """Convert to dictionary, skip serializing the function."""
        return {"type": "function", "name": self.name}


# Custom JSON encoder to handle non-serializable types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SerializableFunction):
            return obj.to_dict()
        return super().default(obj)


# Patch the _save method in HierarchicalMemory to use our encoder
original_save = HierarchicalMemory._save


async def patched_save(self, path):
    """Patched save method to handle SerializableFunction objects."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)

        memory_data = {
            "working": [item.to_dict() for item in self._working_memory],
            "episodic": [item.to_dict() for item in self._episodic_memory],
            "semantic": {k: v.to_dict() for k, v in self._semantic_memory.items()},  # noqa: E501
            "procedural": {k: v.to_dict() for k, v in self._procedural_memory.items()},  # noqa: E501
        }

        with open(path, "w") as f:
            json.dump(memory_data, f, cls=CustomJSONEncoder)

    except Exception as e:
        print(f"Failed to save memory: {e}")


# Apply the patch
HierarchicalMemory._save = patched_save


async def main():
    # Create a memory persistence directory
    memory_dir = Path("./memory_data")
    memory_dir.mkdir(exist_ok=True)

    memory_file = memory_dir / "agent_memory.json"

    # Create a memory manager
    memory_manager = MemoryManager(
        persistence_path=str(memory_file),
        # Limit working memory to most recent 50 items
        working_memory_limit=50,
        # Limit episodic memory to 500 items
        episodic_memory_limit=500,
    )

    # Initialize the memory manager
    async with memory_manager:
        # Add some messages to the memory
        await memory_manager.add_message(
            Message(role="system", content="You are a helpful assistant.")
        )
        await memory_manager.add_message(
            Message(
                role="user",
                content="Can you help me with a programming task?",  # noqa: E501
            )
        )
        await memory_manager.add_message(
            Message(
                role="assistant",
                content=(
                    "Of course! What kind of programming task do you " "need help with?"  # noqa: E501
                ),
            )
        )

        # Store knowledge in semantic memory
        await memory_manager.store_knowledge(
            "python_basics",
            "Python is a high-level, interpreted programming language known "
            "for its readability and versatility.",
            {"category": "programming", "language": "python"},
        )

        await memory_manager.store_knowledge(
            "git_basics",
            "Git is a distributed version control system for tracking changes "
            "in source code during software development.",
            {"category": "tools", "type": "version_control"},
        )

        # Store a procedure in procedural memory
        # Use wrapper to make serializable
        format_code = SerializableFunction(
            lambda code: "\n".join([
                line.strip() for line in code.split("\n") if line.strip()
            ])
        )

        # Store the procedure in memory
        await memory_manager.store_procedure(
            "format_code",
            format_code,
            {"language": "python", "type": "formatter"},  # noqa: E501
        )

        # Add experiences to episodic memory
        await memory_manager.add_experience(
            "User asked about Python dictionaries.",
            {"topic": "python", "subtopic": "dictionaries", "sentiment": "neutral"},  # noqa: E501
        )

        # Demonstrate saving and loading memory
        # Note: Function objects can't be serialized, wrapper will handle it
        await memory_manager.save()
        print(f"Memory saved to {memory_file}")

        # Retrieve messages
        messages = await memory_manager.get_messages()
        print("\nMessages in memory:")
        for msg in messages:
            print(f"- {msg.role}: {msg.content}")

        # Retrieve knowledge
        python_knowledge = await memory_manager.retrieve_knowledge("python_basics")  # noqa: E501
        print(f"\nPython knowledge: {python_knowledge}")

        # Retrieve procedure
        format_procedure = await memory_manager.retrieve_procedure("format_code")  # noqa: E501
        if format_procedure and hasattr(format_procedure, "func"):
            messy_code = """
            def hello_world():
                print('Hello, world!')


            hello_world()
            """
            formatted = format_procedure(messy_code)
            print(f"\nFormatted code:\n{formatted}")

        # Clear memory and verify
        print("\nClearing memory...")
        await memory_manager.clear()

        messages_after_clear = await memory_manager.get_messages()
        print(f"Messages after clear: {len(messages_after_clear)}")

        # Load memory back
        print("\nLoading memory from disk...")
        try:
            await memory_manager.load()

            messages_after_load = await memory_manager.get_messages()
            print(f"Messages after loading: {len(messages_after_load)}")
            for msg in messages_after_load:
                print(f"- {msg.role}: {msg.content}")
        except Exception as e:
            print(f"Note: Functions cannot be restored from disk: {e}")
            print(
                "This is expected behavior as functions are not " "fully serializable."  # noqa: E501
            )


async def demo_advanced():
    """Demonstrate more advanced memory features."""
    print("\nAdvanced memory features:")

    memory = HierarchicalMemory()

    # Add more complex data to memory
    for i in range(10):
        await memory.add_experience(
            f"Experience {i + 1}: The agent performed task {i + 1}",
            {"type": "task", "task_id": i + 1, "priority": i % 3},
        )

    # Filter experiences by metadata
    high_priority = await memory.retrieve_experiences(
        filter_fn=lambda item: item.metadata.get("priority") == 2, max_count=5
    )

    print("\nHigh priority experiences:")
    for exp in high_priority:
        print(f"- {exp}")

    # If we had an embeddings provider, we could also do semantic search
    print("\nNote: Semantic search requires an embeddings provider.")
    print(
        "To enable semantic search, configure an embeddings provider "
        "when creating the memory."
    )


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())

    # Demonstrate advanced features - use asyncio.run for new event loop
    asyncio.run(demo_advanced())
