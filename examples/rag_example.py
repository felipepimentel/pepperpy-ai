"""Example demonstrating RAG (Retrieval Augmented Generation) functionality.

This example shows how to use PepperPy's fluent API for RAG operations.
"""

import asyncio
import os
from pathlib import Path
from typing import cast

from pepperpy import PepperPy, plugin_manager
from pepperpy.rag.base import Document, RAGProvider

# Setup paths
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main() -> None:
    """Run the example."""
    print("RAG Example")
    print("=" * 50)

    # Create RAG provider using the plugin manager
    rag_provider = cast(RAGProvider, plugin_manager.create_provider("rag", "memory"))

    # Initialize PepperPy with RAG support
    async with PepperPy().with_rag(rag_provider) as pepper:
        # Check if we have documents
        results = await pepper.search("", limit=10)
        print(f"\nFound {len(results)} documents in database")

        # Add sample documents if needed
        if len(results) == 0:
            print("\nAdding sample documents...")
            # Create documents to add
            docs = [
                Document(
                    text="PepperPy is a Python framework for building AI applications",
                    metadata={"type": "framework", "language": "python"},
                ),
                Document(
                    text="RAG (Retrieval Augmented Generation) enhances LLM responses with relevant context",
                    metadata={"type": "concept", "field": "ai"},
                ),
                Document(
                    text="Vector databases store and search high-dimensional vectors efficiently",
                    metadata={"type": "technology", "field": "databases"},
                ),
            ]

            # Store documents using pepper's add_documents method
            await pepper.add_documents(docs)

            results = await pepper.search("", limit=10)
            print(f"Added {len(results)} documents")

        # Search example
        print("\nSearching for 'Python framework'...")
        results = await pepper.search("Python framework", limit=5)

        # Print results
        print("\nSearch results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.document.text}")
            print(f"   Type: {result.document.metadata.get('type')}")
            print(f"   Field: {result.document.metadata.get('field', 'N/A')}")


if __name__ == "__main__":
    # Uses memory provider that doesn't require API keys
    asyncio.run(main())
