"""Complete example of PepperPy usage."""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy


async def simple_chat_example():
    """Example of simple chat with LLM."""
    print("\n=== Simple Chat Example ===")

    # Initialize PepperPy with fluent API
    async with PepperPy().with_llm() as pepperpy:
        # Simple question
        result = await pepperpy.ask("What is Python?")
        print("\nResponse:", result.content)


async def rag_example():
    """Example of RAG operations."""
    print("\n=== RAG Example ===")

    # Initialize PepperPy with RAG support
    async with PepperPy().with_llm().with_rag() as pepperpy:
        # Create and learn documents one by one
        docs_texts = [
            "Python is a high-level programming language.",
            "Python was created by Guido van Rossum.",
            "Python is known for its simple syntax.",
        ]

        # Store documents
        for doc_text in docs_texts:
            await pepperpy.learn(doc_text)

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

    # Initialize PepperPy with storage support
    async with PepperPy().with_llm().with_rag().with_storage() as pepperpy:
        # Load file
        await pepperpy.remember("examples/output/docs/python.md")

        # Search and generate
        response = await pepperpy.ask("What is Python used for?")
        print("\nResponse:", response.content)


async def interactive_chat_example():
    """Example of interactive chat with context."""
    print("\n=== Interactive Chat Example ===")

    # Initialize PepperPy with both LLM and RAG capabilities
    async with PepperPy().with_llm().with_rag() as pepperpy:
        # Add knowledge
        knowledge_texts = [
            "PepperPy is a Python framework for building AI applications.",
            "It combines RAG and LLM capabilities.",
            "It has a simple, fluent API.",
        ]

        # Learn each piece of knowledge
        for text in knowledge_texts:
            await pepperpy.learn(text)

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
    # Required environment variables in .env file:
    # PEPPERPY_LLM__PROVIDER=openai
    # PEPPERPY_LLM__OPENAI__API_KEY=your-api-key
    # PEPPERPY_RAG__PROVIDER=chroma
    # PEPPERPY_EMBEDDINGS__PROVIDER=openai
    # PEPPERPY_STORAGE__PROVIDER=local
    asyncio.run(main())
