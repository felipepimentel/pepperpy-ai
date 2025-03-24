"""Example demonstrating RAG context usage with vector storage and similarity search."""

import asyncio
import numpy as np
import random

from pepperpy.embeddings.base import EmbeddingProvider
from pepperpy.rag import ChromaProvider, Document, Query, RAGContext


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider that generates random embeddings."""

    def __init__(self, dimension: int = 10):
        """Initialize the mock provider.
        
        Args:
            dimension: Dimensionality of the embeddings
        """
        super().__init__()
        self.dimension = dimension
        self.name = "mock"

    def get_dimensions(self) -> int:
        """Get the embedding dimensions.
        
        Returns:
            Number of dimensions in the embeddings
        """
        return self.dimension

    async def embed_text(self, text: str | list[str]) -> list[float] | list[list[float]]:
        """Generate a mock embedding for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            A random embedding vector
        """
        if isinstance(text, str):
            return [random.uniform(-1, 1) for _ in range(self.dimension)]
        return [[random.uniform(-1, 1) for _ in range(self.dimension)] for _ in text]


async def main():
    """Run the example."""
    # Create providers
    embedding_provider = MockEmbeddingProvider(dimension=128)  # Smaller dimension for readability
    rag_provider = ChromaProvider(collection_name="test_collection")

    # Create documents
    documents = [
        Document(
            content="Vector embeddings are numerical representations of data.",
            metadata={"source": "example", "type": "definition"}
        ),
        Document(
            content="Vector databases store and query vector embeddings efficiently.",
            metadata={"source": "example", "type": "explanation"}
        ),
        Document(
            content="Semantic search uses vector similarity to find relevant results.",
            metadata={"source": "example", "type": "explanation"}
        )
    ]

    # Create context
    context = RAGContext(
        embedding_provider=embedding_provider,
        provider=rag_provider
    )

    print("\nAdding documents...")
    added_docs = await context.add_documents(documents)
    print(f"Added {len(added_docs)} documents")

    # Perform searches
    queries = [
        "What are vector embeddings?",
        "How do vector databases work?",
        "What is semantic search?"
    ]

    print("\nPerforming searches...")
    for query in queries:
        print(f"\nQuery: {query}")
        results = await context.search(query, limit=1)
        for doc in results.documents:
            print(f"Result: {doc.content}")
            print(f"Metadata: {doc.metadata}")
            if results.scores:
                print(f"Score: {results.scores[results.documents.index(doc)]:.3f}")


if __name__ == "__main__":
    asyncio.run(main()) 