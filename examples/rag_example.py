"""Example demonstrating RAG (Retrieval Augmented Generation) functionality.

This example shows how to use PepperPy's fluent API for RAG operations.
"""

import asyncio
import os
from pathlib import Path

import numpy as np

from pepperpy import PepperPy

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


async def main() -> None:
    """Run the example."""
    print("RAG Example")
    print("=" * 50)

    # Create embeddings generator
    embeddings = MockEmbeddings()

    # Initialize PepperPy with RAG
    async with PepperPy().with_rag(provider="sqlite", database_path=db_path) as pepper:
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
                    embeddings=embeddings.generate("PepperPy is a Python framework"),
                )
                .with_document(
                    text="RAG (Retrieval Augmented Generation) enhances LLM responses with relevant context",
                    metadata={"type": "concept", "field": "ai"},
                    embeddings=embeddings.generate("RAG enhances LLM responses"),
                )
                .with_document(
                    text="Vector databases store and search high-dimensional vectors efficiently",
                    metadata={"type": "technology", "field": "databases"},
                    embeddings=embeddings.generate("Vector databases for search"),
                )
                .store()
            )

            results = await pepper.rag.search("").generate()
            print(f"Added {len(results)} documents")

        # Search example
        print("\nSearching for 'Python framework'...")
        results = await (
            pepper.rag.search("Python framework")
            .with_embeddings(embeddings.generate("Python framework"))
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
    asyncio.run(main())
