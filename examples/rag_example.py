"""Example demonstrating RAG (Retrieval Augmented Generation) functionality.

This example shows how to use PepperPy's fluent API for RAG operations.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Setup paths
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main() -> None:
    """Run the example."""
    print("RAG Example")
    print("=" * 50)

    # Initialize PepperPy with RAG and embeddings support
    # Provider configuration comes from environment variables
    async with PepperPy().with_rag().with_embeddings() as pepper:
        # Check if we have documents
        results = await pepper.rag.search("").generate()
        print(f"\nFound {len(results)} documents in database")

        # Add sample documents if needed
        if len(results) == 0:
            print("\nAdding sample documents...")
            await (
                pepper.rag.with_document(
                    text="PepperPy is a Python framework for building AI applications",
                    metadata={"type": "framework", "language": "python"},
                )
                .with_document(
                    text="RAG (Retrieval Augmented Generation) enhances LLM responses with relevant context",
                    metadata={"type": "concept", "field": "ai"},
                )
                .with_document(
                    text="Vector databases store and search high-dimensional vectors efficiently",
                    metadata={"type": "technology", "field": "databases"},
                )
                .with_auto_embeddings()  # Let PepperPy handle embeddings
                .store()
            )

            results = await pepper.rag.search("").generate()
            print(f"Added {len(results)} documents")

        # Search example
        print("\nSearching for 'Python framework'...")
        results = await (
            pepper.rag.search("Python framework")
            .with_auto_embeddings()  # Let PepperPy handle embeddings
            .generate()
        )

        # Print results
        print("\nSearch results:")
        for i, result in enumerate(results, 1):
            doc = result.to_document()
            print(f"\n{i}. {doc.text}")
            print(f"   Type: {doc.metadata.get('type')}")
            print(f"   Field: {doc.metadata.get('field', 'N/A')}")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_RAG__PROVIDER=chroma
    # PEPPERPY_EMBEDDINGS__PROVIDER=openai
    # PEPPERPY_EMBEDDINGS__API_KEY=your_api_key
    asyncio.run(main())
