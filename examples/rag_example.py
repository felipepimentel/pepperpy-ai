"""Example demonstrating RAG (Retrieval Augmented Generation) functionality.

This example shows how to:
1. Create a RAG provider
2. Add sample documents
3. Search for relevant documents
"""

import asyncio
import os
from pathlib import Path

import numpy as np

from pepperpy.rag import Document, Query, create_provider

# Setup paths
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Database path
db_path = str(OUTPUT_DIR / "pepperpy.db")


class MockEmbeddings:
    """Mock embeddings generator for demonstration."""

    def __init__(self, dim: int = 384):
        """Initialize mock embeddings.

        Args:
            dim: Dimension of embeddings
        """
        self.dim = dim

    def generate(self, text: str) -> list[float]:
        """Generate mock embeddings.

        Args:
            text: Text to generate embeddings for

        Returns:
            Mock embedding vector
        """
        # Generate random vector
        vector = np.random.randn(self.dim)
        # Normalize
        vector = vector / np.linalg.norm(vector)
        return vector.tolist()


async def check_database(provider) -> int:
    """Check if database exists and return document count.

    Args:
        provider: RAG provider

    Returns:
        Number of documents in database
    """
    # Search for all documents with empty query
    results = await provider.search("", limit=100)
    return len(results)


async def add_sample_documents(provider, embeddings: MockEmbeddings) -> None:
    """Add sample documents to database.

    Args:
        provider: RAG provider
        embeddings: Embeddings generator
    """
    # Sample documents
    documents = [
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

    # Add embeddings
    for doc in documents:
        doc.update({"embeddings": embeddings.generate(doc.text)})

    # Store documents
    await provider.store(documents)


async def main():
    """Run the example."""
    # Create provider
    provider = create_provider("sqlite", database_path=db_path)
    await provider.initialize()

    try:
        # Check database
        count = await check_database(provider)
        print(f"Found {count} documents in database")

        # Add documents if needed
        if count == 0:
            print("Adding sample documents...")
            embeddings = MockEmbeddings()
            await add_sample_documents(provider, embeddings)
            count = await check_database(provider)
            print(f"Added {count} documents")

        # Search example
        print("\nSearching for 'Python framework'...")
        query = Query(
            text="Python framework",
            embeddings=MockEmbeddings().generate("Python framework"),
        )
        results = await provider.search(query)

        # Print results
        print("\nSearch results:")
        for i, result in enumerate(results, 1):
            doc = result.to_document()
            print(f"\n{i}. {doc.text}")
            print(f"   Type: {doc.metadata.get('type')}")
            print(f"   Field: {doc.metadata.get('field', 'N/A')}")

    finally:
        # Cleanup
        await provider.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
