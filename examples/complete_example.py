"""Complete example of PepperPy usage."""

import asyncio
import os
from pathlib import Path

from pepperpy import (
    Document,
    GenerationResult,
    PepperPy,
)
from pepperpy.core.config import Config


async def simple_chat_example():
    """Example of simple chat with LLM."""
    print("\n=== Simple Chat Example ===")

    # Configure with custom options
    config = Config({
        "llm": {
            "provider": "openai",
            "config": {"model": "gpt-3.5-turbo", "temperature": 0.7},
        }
    }).to_dict()

    # Simple question
    async with PepperPy(config) as pepperpy:
        pepperpy.with_llm()  # Use config settings
        result: GenerationResult = await pepperpy.send("What is Python?")
        print("\nResponse:", result.content)


async def rag_example():
    """Example of RAG operations."""
    print("\n=== RAG Example ===")

    # Configure with custom options
    config = Config({
        "llm": {"provider": "openai"},
        "rag": {"provider": "chroma"},
        "embeddings": {"provider": "openai"},
    }).to_dict()

    # Add knowledge and ask questions
    async with PepperPy(config) as pepperpy:
        pepperpy.with_llm().with_rag()

        # Create documents
        docs = [
            Document(text="Python is a high-level programming language."),
            Document(text="Python was created by Guido van Rossum."),
            Document(text="Python is known for its simple syntax."),
        ]

        # Store documents
        await pepperpy.learn(docs)

        # Search and generate
        response = await pepperpy.ask("Who created Python?")
        print("\nResponse:", response.content)


async def file_knowledge_example():
    """Example of loading knowledge from files."""
    print("\n=== File Knowledge Example ===")

    # Create a sample markdown file
    docs_dir = Path("examples/output/docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    with open(docs_dir / "python.md", "w") as f:
        f.write("""
# Python Programming

Python is a versatile language used in:
- Web development
- Data science
- AI/ML
- Automation
""")

    # Configure with storage
    config = Config({
        "llm": {"provider": "openai"},
        "rag": {"provider": "chroma"},
        "embeddings": {"provider": "openai"},
        "storage": {"provider": "local"},
    }).to_dict()

    # Load and query knowledge
    async with PepperPy(config) as pepperpy:
        pepperpy.with_llm().with_rag().with_storage()

        # Load file
        await pepperpy.remember("examples/output/docs/python.md")

        # Search and generate
        response = await pepperpy.ask("What is Python used for?")
        print("\nResponse:", response.content)


async def interactive_chat_example():
    """Example of interactive chat with context."""
    print("\n=== Interactive Chat Example ===")

    config = Config({
        "llm": {
            "provider": "openai",
            "config": {"model": "gpt-3.5-turbo", "temperature": 0.7},
        },
        "rag": {"provider": "chroma"},
        "embeddings": {"provider": "openai"},
    }).to_dict()

    async with PepperPy(config) as pepperpy:
        pepperpy.with_llm().with_rag()

        # Add knowledge
        docs = [
            Document(
                text="PepperPy is a Python framework for building AI applications."
            ),
            Document(text="It combines RAG and LLM capabilities."),
            Document(text="It has a simple, fluent API."),
        ]
        await pepperpy.learn(docs)

        # Simulate conversation
        messages = [
            "What is PepperPy?",
            "How does it combine RAG and LLM?",
            "Show me a simple example.",
        ]

        for msg in messages:
            print(f"\nUser: {msg}")
            response = await pepperpy.ask(msg)
            print(f"Assistant: {response.content}")


async def main():
    """Run all examples."""
    # Create output directory
    os.makedirs("examples/output", exist_ok=True)

    # Run examples
    await simple_chat_example()
    await rag_example()
    await file_knowledge_example()
    await interactive_chat_example()


if __name__ == "__main__":
    asyncio.run(main())
