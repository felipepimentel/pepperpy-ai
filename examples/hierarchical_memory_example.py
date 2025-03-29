"""Example demonstrating hierarchical memory capabilities in PepperPy.

This example shows how to use a hierarchical memory system with:
- Working memory (recent interactions)
- Episodic memory (experiences)
- Semantic memory (knowledge)
- Procedural memory (functions/procedures)
"""

import asyncio
import json
from pathlib import Path

from pepperpy import PepperPy
from pepperpy.agents.base import Message


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


async def basic_memory_example() -> None:
    """Demonstrate basic memory operations."""
    print("\n=== Basic Memory Operations ===")

    # Create memory directory
    memory_dir = Path("./memory_data")
    memory_dir.mkdir(exist_ok=True)
    memory_file = memory_dir / "agent_memory.json"

    # Initialize PepperPy with memory support
    async with (
        PepperPy()
        .with_memory()
        .with_memory_config(
            persistence_path=str(memory_file),
            working_memory_limit=50,
            episodic_memory_limit=500,
        )
    ) as pepper:
        # Add conversation messages
        await (
            pepper.memory.add_message(
                Message(role="system", content="You are a helpful assistant.")
            )
            .add_message(
                Message(role="user", content="Can you help me with a programming task?")
            )
            .add_message(
                Message(
                    role="assistant",
                    content="Of course! What kind of programming task do you need help with?",
                )
            )
            .execute()
        )

        # Store knowledge in semantic memory
        await (
            pepper.memory.store_knowledge(
                "python_basics",
                "Python is a high-level, interpreted programming language known for its readability and versatility.",
                metadata={"category": "programming", "language": "python"},
            )
            .store_knowledge(
                "git_basics",
                "Git is a distributed version control system for tracking changes in source code during software development.",
                metadata={"category": "tools", "type": "version_control"},
            )
            .execute()
        )

        # Store procedure in procedural memory
        format_code = SerializableFunction(
            lambda code: "\n".join([
                line.strip() for line in code.split("\n") if line.strip()
            ])
        )

        await pepper.memory.store_procedure(
            "format_code",
            format_code,
            metadata={"language": "python", "type": "formatter"},
        ).execute()

        # Add experience to episodic memory
        await pepper.memory.add_experience(
            "User asked about Python dictionaries.",
            metadata={
                "topic": "python",
                "subtopic": "dictionaries",
                "sentiment": "neutral",
            },
        ).execute()

        # Save memory state
        await pepper.memory.save()
        print(f"Memory saved to {memory_file}")

        # Retrieve and display messages
        messages = await pepper.memory.get_messages()
        print("\nMessages in memory:")
        for msg in messages:
            print(f"- {msg.role}: {msg.content}")

        # Retrieve knowledge
        python_knowledge = await pepper.memory.retrieve_knowledge("python_basics")
        print(f"\nPython knowledge: {python_knowledge}")

        # Retrieve and use procedure
        format_procedure = await pepper.memory.retrieve_procedure("format_code")
        if format_procedure and hasattr(format_procedure, "func"):
            messy_code = """
            def hello_world():
                print('Hello, world!')


            hello_world()
            """
            formatted = format_procedure(messy_code)
            print(f"\nFormatted code:\n{formatted}")

        # Clear and reload memory
        print("\nClearing memory...")
        await pepper.memory.clear()

        messages_after_clear = await pepper.memory.get_messages()
        print(f"Messages after clear: {len(messages_after_clear)}")

        print("\nLoading memory from disk...")
        try:
            await pepper.memory.load()
            messages_after_load = await pepper.memory.get_messages()
            print(f"Messages after loading: {len(messages_after_load)}")
            for msg in messages_after_load:
                print(f"- {msg.role}: {msg.content}")
        except Exception as e:
            print(f"Note: Functions cannot be restored from disk: {e}")
            print("This is expected behavior as functions are not fully serializable.")


async def advanced_memory_example() -> None:
    """Demonstrate advanced memory features."""
    print("\n=== Advanced Memory Features ===")

    async with PepperPy().with_memory().with_embeddings() as pepper:
        # Add experiences with metadata
        await pepper.memory.batch_experiences([
            {
                "content": f"Experience {i + 1}: The agent performed task {i + 1}",
                "metadata": {"type": "task", "task_id": i + 1, "priority": i % 3},
            }
            for i in range(10)
        ]).execute()

        # Filter experiences by metadata
        high_priority = await (
            pepper.memory.retrieve_experiences()
            .filter(lambda item: item.metadata.get("priority") == 2)
            .limit(5)
            .execute()
        )

        print("\nHigh priority experiences:")
        for exp in high_priority:
            print(f"- {exp}")

        # Semantic search (requires embeddings provider)
        similar = await (
            pepper.memory.search("agent performing complex tasks").limit(3).execute()
        )

        print("\nSemantically similar experiences:")
        for exp in similar:
            print(f"- {exp}")


async def main() -> None:
    """Run memory system examples."""
    print("Starting hierarchical memory examples...\n")
    await basic_memory_example()
    await advanced_memory_example()


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_MEMORY__PROVIDER=memory
    # PEPPERPY_EMBEDDINGS__PROVIDER=openai
    # PEPPERPY_EMBEDDINGS__API_KEY=your_api_key
    asyncio.run(main())
