"""
Example demonstrating the use of hierarchical memory in an agent.

This example shows how to set up and use a hierarchical memory system
with working, episodic, semantic, and procedural memory.
"""

import asyncio
from pathlib import Path

from pepperpy.agents.base import Message
from pepperpy.agents.hierarchical_memory import HierarchicalMemory, MemoryManager


async def main():
    # Create a memory persistence directory
    memory_dir = Path("./memory_data")
    memory_dir.mkdir(exist_ok=True)

    memory_file = memory_dir / "agent_memory.json"

    # Create a memory manager
    memory_manager = MemoryManager(
        persistence_path=str(memory_file),
        working_memory_limit=50,  # Limit working memory to most recent 50 items
        episodic_memory_limit=500,  # Limit episodic memory to 500 items
    )

    # Initialize the memory manager
    async with memory_manager:
        # Add some messages to the memory
        await memory_manager.add_message(
            Message(role="system", content="You are a helpful assistant.")
        )
        await memory_manager.add_message(
            Message(role="user", content="Can you help me with a programming task?")
        )
        await memory_manager.add_message(
            Message(
                role="assistant",
                content="Of course! What kind of programming task do you need help with?",
            )
        )

        # Store knowledge in semantic memory
        await memory_manager.store_knowledge(
            "python_basics",
            "Python is a high-level, interpreted programming language known for its readability and versatility.",
            {"category": "programming", "language": "python"},
        )

        await memory_manager.store_knowledge(
            "git_basics",
            "Git is a distributed version control system for tracking changes in source code during software development.",
            {"category": "tools", "type": "version_control"},
        )

        # Store a procedure in procedural memory
        await memory_manager.store_procedure(
            "format_code",
            lambda code: "\n".join([
                line.strip() for line in code.split("\n") if line.strip()
            ]),
            {"language": "python", "type": "formatter"},
        )

        # Add experiences to episodic memory
        await memory_manager.add_experience(
            "User asked about Python dictionaries.",
            {"topic": "python", "subtopic": "dictionaries", "sentiment": "neutral"},
        )

        # Demonstrate saving and loading memory
        await memory_manager.save()
        print(f"Memory saved to {memory_file}")

        # Retrieve messages
        messages = await memory_manager.get_messages()
        print("\nMessages in memory:")
        for msg in messages:
            print(f"- {msg.role}: {msg.content}")

        # Retrieve knowledge
        python_knowledge = await memory_manager.retrieve_knowledge("python_basics")
        print(f"\nPython knowledge: {python_knowledge}")

        # Retrieve procedure
        format_procedure = await memory_manager.retrieve_procedure("format_code")
        if format_procedure:
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
        await memory_manager.load()

        messages_after_load = await memory_manager.get_messages()
        print(f"Messages after loading: {len(messages_after_load)}")
        for msg in messages_after_load:
            print(f"- {msg.role}: {msg.content}")


def demonstrate_filter_and_search():
    """Demonstrate more advanced memory features."""
    print("\nAdvanced memory features:")
    loop = asyncio.get_event_loop()

    async def demo_advanced():
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
            "To enable semantic search, configure an embeddings provider when creating the memory."
        )

    loop.run_until_complete(demo_advanced())


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())

    # Demonstrate more advanced features
    demonstrate_filter_and_search()
