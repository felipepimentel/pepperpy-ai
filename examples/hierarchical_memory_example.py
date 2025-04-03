"""Example demonstrating hierarchical memory capabilities in PepperPy.

This example shows how to use PepperPy's built-in memory system for storing and retrieving
different types of knowledge with a hierarchical structure.
"""

import asyncio

from pepperpy.pepperpy import MessageRole, PepperPy


async def demonstrate_memory_capabilities() -> None:
    """Demonstrate PepperPy's advanced memory capabilities."""
    print("\n=== PepperPy Hierarchical Memory System ===")

    # Initialize PepperPy with default configuration
    pepper = PepperPy()
    await pepper.initialize()

    try:
        # Create our repository with memory support
        repo = pepper.create_memory_repository()

        print("\nStoring documents in memory...")

        # Add semantic knowledge (factual information)
        await repo.store_knowledge(
            "Python is a high-level, interpreted programming language known for its readability and versatility.",
            category="programming",
            tags=["python", "language"],
        )

        await repo.store_knowledge(
            "Git is a distributed version control system for tracking changes in source code during software development.",
            category="tools",
            tags=["git", "version-control"],
        )

        # Add procedural knowledge (how to do things)
        await repo.store_procedure(
            "Function to format code by stripping whitespace and fixing indentation.",
            language="python",
            type="formatter",
        )

        # Add episodic memory (experiences)
        await repo.store_experience(
            "User asked about Python dictionaries and how to use them effectively.",
            topic="python",
            subtopic="dictionaries",
        )

        # Search operations
        print("\nSearching memory for 'Python'...")
        python_results = await repo.search("Python")

        if python_results:
            print(f"Found {len(python_results)} documents about Python:")
            for result in python_results:
                print(f"- {result.text[:50]}...")

        # Retrieve by memory type
        print("\nDemonstrating hierarchical memory access:")

        # Get procedural memories
        print("\nProcedural memory (functions/procedures):")
        procedures = await repo.get_procedures()
        for proc in procedures:
            print(f"- {proc.text}")

        # Get episodic memories
        print("\nEpisodic memory (experiences):")
        experiences = await repo.get_experiences()
        for exp in experiences:
            print(f"- {exp.text}")

        # Get semantic knowledge
        print("\nSemantic memory (knowledge):")
        knowledge = await repo.get_knowledge()
        for item in knowledge:
            print(f"- [{item.metadata.get('category', 'general')}] {item.text}")

        # Export memory to file (automatically handled by PepperPy)
        memory_file = await repo.export_memory("memory_data.json")
        print(f"\nMemory exported to {memory_file}")

    finally:
        # Clean up resources
        await pepper.cleanup()


async def demonstrate_memory_with_chat() -> None:
    """Demonstrate how memory enhances chat capabilities."""
    print("\n=== Memory-Enhanced Chat ===")

    # Initialize PepperPy
    pepper = PepperPy()
    await pepper.initialize()

    try:
        # Create repository with chat memory
        repo = pepper.create_memory_repository()

        # Store some background knowledge
        await repo.store_knowledge(
            "Python dictionaries are key-value stores that provide O(1) lookup time.",
            category="programming",
            tags=["python", "dictionaries"],
        )

        # Chat interface with memory enhancement
        pepper.chat.with_message(
            MessageRole.SYSTEM,
            "You are a helpful assistant. Use your knowledge about Python.",
        )

        # Ask a question that can be answered with the stored knowledge
        print("\nAsking about Python dictionaries (with memory):")
        response = (
            await pepper.chat.with_message(
                MessageRole.USER, "Tell me about Python dictionaries"
            )
            .with_memory(repo)
            .generate()
        )

        print(f"Assistant: {response}")

    finally:
        await pepper.cleanup()


async def main() -> None:
    """Run examples demonstrating PepperPy's memory capabilities."""
    print("Starting PepperPy Memory Examples...\n")

    try:
        await demonstrate_memory_capabilities()
        # Uncomment to run chat example when LLM is configured
        # await demonstrate_memory_with_chat()
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
