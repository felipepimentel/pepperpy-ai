"""
Example demonstrating the in-memory RAG provider.

This example shows how to use the lightweight in-memory RAG provider
for simple retrieval augmented generation tasks, without requiring
any external dependencies or databases.
"""

import asyncio
from typing import Dict, List

import numpy as np

from pepperpy.rag.providers.memory import InMemoryProvider


# Simple mock embeddings function to avoid requiring actual embedding models
class MockEmbeddings:
    """Simple mock embeddings generator for demonstration purposes.

    This creates random embeddings of specified dimension that maintain
    some semantic meaning (similar texts get similar embeddings).
    """

    def __init__(self, dim: int = 10):
        """Initialize the mock embeddings generator."""
        self.dim = dim
        self.word_vectors: Dict[str, List[float]] = {}

    def _get_word_vector(self, word: str) -> List[float]:
        """Get or create a vector for a word."""
        if word not in self.word_vectors:
            # Use word hash as seed for reproducibility
            seed = sum(ord(c) for c in word)
            np.random.seed(seed)
            self.word_vectors[word] = np.random.randn(self.dim).tolist()
        return self.word_vectors[word]

    async def embed_query(self, text: str) -> List[float]:
        """Generate embeddings for a text string."""
        # Simple averaging of word vectors
        words = text.lower().split()
        if not words:
            return np.zeros(self.dim).tolist()

        vectors = [self._get_word_vector(word) for word in words]
        return (np.mean(vectors, axis=0) + np.random.randn(self.dim) * 0.1).tolist()


async def main():
    """Run the example."""
    print("In-Memory RAG Provider Example")
    print("==============================\n")

    # Create mock embeddings function
    embeddings = MockEmbeddings(dim=10)

    # Create in-memory provider
    rag = InMemoryProvider(collection_name="example")
    await rag.initialize()

    # Add documents
    print("Adding documents...")
    documents = [
        "Python is a high-level programming language known for its readability and simple syntax.",
        "Machine learning is a subset of artificial intelligence focused on building systems that learn from data.",
        "Natural Language Processing (NLP) enables computers to understand and generate human language.",
        "Python libraries like TensorFlow and PyTorch are commonly used for machine learning tasks.",
        "Data preprocessing is a crucial step in preparing data for machine learning models.",
        "Deep learning models use neural networks with multiple layers to learn representations of data.",
        "Git is a distributed version control system for tracking changes in source code.",
        "Docker containers package code and dependencies together for consistent deployment.",
        "APIs (Application Programming Interfaces) allow different software systems to communicate.",
        "Cloud computing provides on-demand computing resources over the internet.",
    ]

    metadatas = [
        {"topic": "programming", "category": "language"},
        {"topic": "ai", "category": "concept"},
        {"topic": "ai", "category": "nlp"},
        {"topic": "programming", "category": "libraries"},
        {"topic": "ai", "category": "process"},
        {"topic": "ai", "category": "technique"},
        {"topic": "tools", "category": "version control"},
        {"topic": "tools", "category": "containerization"},
        {"topic": "programming", "category": "integration"},
        {"topic": "infrastructure", "category": "cloud"},
    ]

    # Add documents
    doc_ids = await rag.add_texts(documents, metadatas)
    print(f"Added {len(doc_ids)} documents")

    # Generate and add embeddings
    print("Generating embeddings...")
    doc_embeddings = []
    for doc in documents:
        embedding = await embeddings.embed_query(doc)
        doc_embeddings.append(embedding)

    # Add embeddings to documents
    await rag.add_embeddings(doc_ids, doc_embeddings)
    print("Embeddings added")

    # Perform text search
    print("\n1. Basic text search:")
    query = "python programming"
    results = await rag.search_documents(query, limit=3)

    for i, result in enumerate(results):
        print(f"\nResult {i + 1} (score: {result['score']:.2f}):")
        print(f"Text: {result['text']}")
        print(f"Metadata: {result['metadata']}")

    # Perform vector search with embeddings
    print("\n2. Vector search:")
    query = "machine learning and neural networks"
    query_embedding = await embeddings.embed_query(query)

    results = await rag.search_documents(
        query, limit=3, query_embedding=query_embedding
    )

    for i, result in enumerate(results):
        print(f"\nResult {i + 1} (score: {result['score']:.2f}):")
        print(f"Text: {result['text']}")
        print(f"Metadata: {result['metadata']}")

    # Filtering by metadata
    print("\n3. Search with metadata filter:")
    results = await rag.search_documents(
        query="tools", limit=3, filter_metadata={"category": "containerization"}
    )

    for i, result in enumerate(results):
        print(f"\nResult {i + 1} (score: {result['score']:.2f}):")
        print(f"Text: {result['text']}")
        print(f"Metadata: {result['metadata']}")

    # List all documents
    print("\n4. All documents in the store:")
    all_docs = await rag.list_documents()
    print(f"Total documents: {len(all_docs)}")

    # Get stats
    stats = await rag.get_stats()
    print("\nStats:", stats)

    # Clean up
    await rag.clear()
    print("\nMemory cleared")


if __name__ == "__main__":
    asyncio.run(main())
