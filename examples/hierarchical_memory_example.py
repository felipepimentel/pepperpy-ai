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

from pepperpy import MessageRole, PepperPy
from pepperpy.embeddings import create_provider as create_embeddings_provider
from pepperpy.llm import create_provider as create_llm_provider
from pepperpy.rag import create_provider as create_rag_provider


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

    # Create providers
    memory_provider = create_rag_provider(
        "memory", collection_name="agent_memory", persistence_path=str(memory_file)
    )

    # Create LLM provider
    llm_provider = create_llm_provider("openrouter")

    # Initialize PepperPy with RAG and LLM support
    async with PepperPy().with_rag(memory_provider).with_llm(llm_provider) as pepper:
        # Add conversation messages
        # Note: Using MessageRole enum for proper typing
        await (
            pepper.chat.with_message(MessageRole.SYSTEM, "You are a helpful assistant.")
            .with_message(MessageRole.USER, "Can you help me with a programming task?")
            .with_message(
                MessageRole.ASSISTANT,
                "Of course! What kind of programming task do you need help with?",
            )
            .generate()
        )

        # Store knowledge as documents directly through the provider
        print("\nStoring documents in memory...")

        # Python basics
        await memory_provider.store_document(
            text="Python is a high-level, interpreted programming language known for its readability and versatility.",
            metadata={
                "category": "programming",
                "language": "python",
                "id": "python_basics",
            },
        )

        # Git basics
        await memory_provider.store_document(
            text="Git is a distributed version control system for tracking changes in source code during software development.",
            metadata={
                "category": "tools",
                "type": "version_control",
                "id": "git_basics",
            },
        )

        # Format code procedure
        await memory_provider.store_document(
            text="Function to format code by stripping whitespace",
            metadata={
                "language": "python",
                "type": "formatter",
                "id": "format_code_procedure",
            },
        )

        # Python dictionaries experience
        await memory_provider.store_document(
            text="User asked about Python dictionaries.",
            metadata={
                "topic": "python",
                "subtopic": "dictionaries",
                "sentiment": "neutral",
                "id": "experience_python_dictionaries",
            },
        )

        # Retrieve knowledge
        print("\nQuerying about Python...")
        python_results = await memory_provider.search_documents(
            "Python programming language", limit=1
        )

        if python_results:
            python_knowledge = python_results[0].get("text", "")
            print(f"Python knowledge: {python_knowledge}")

        # Simulate clearing memory by searching for different content
        print("\nRetrieving programming documents...")
        results = await memory_provider.search_documents("programming", limit=5)

        print(f"Documents found: {len(results)}")
        for doc in results:
            text = doc.get("text", "")
            print(f"- {text[:50]}...")


async def advanced_memory_example() -> None:
    """Demonstrate advanced memory features."""
    print("\n=== Advanced Memory Features ===")

    # Create providers
    memory_provider = create_rag_provider("memory", collection_name="agent_memory")
    embeddings_provider = create_embeddings_provider("openrouter")
    llm_provider = create_llm_provider("openrouter")

    async with PepperPy().with_rag(memory_provider).with_llm(llm_provider) as pepper:
        # Add experiences as documents
        print("\nStoring experience documents...")
        for i in range(10):
            await memory_provider.store_document(
                text=f"Experience {i + 1}: The agent performed task {i + 1}",
                metadata={
                    "type": "task",
                    "task_id": i + 1,
                    "priority": i % 3,
                    "id": f"experience_{i}",
                },
            )

        # Filter experiences by metadata (using priority 2)
        print("\nSearching for high priority experiences (priority=2)...")
        high_priority_results = await memory_provider.search_documents(
            "agent performing task", limit=5, filter_metadata={"priority": 2}
        )

        print("High priority experiences:")
        for result in high_priority_results:
            print(f"- {result.get('text', '')}")

        # Semantic search
        print("\nSemantic search for complex tasks...")
        similar_results = await memory_provider.search_documents(
            "agent performing complex tasks", limit=3
        )

        print("Semantically similar experiences:")
        for result in similar_results:
            print(f"- {result.get('text', '')}")


async def main() -> None:
    """Run memory system examples."""
    print("Starting hierarchical memory examples...\n")
    await basic_memory_example()
    await advanced_memory_example()


if __name__ == "__main__":
    # Using file memory provider and openrouter embeddings (configured in .env)
    asyncio.run(main())
