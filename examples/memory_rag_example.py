#!/usr/bin/env python3
"""
Example demonstrating in-memory RAG capabilities in PepperPy.

This example shows how to use the lightweight in-memory RAG provider
for simple retrieval augmented generation tasks, without requiring
any external dependencies or databases.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SearchResult:
    """Search result from RAG provider."""

    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class MockRAGBuilder:
    """Mock builder for RAG functionality."""

    def __init__(self, pepper):
        self.pepper = pepper
        self.documents = []
        self.search_query = None

    async def add_documents(self, documents: List[str]) -> "MockRAGBuilder":
        """Add documents to the RAG provider."""
        print(f"[Memory RAG] Adding {len(documents)} documents")
        self.documents.extend(documents)
        return self

    async def store(self) -> "MockRAGBuilder":
        """Store documents in the RAG provider."""
        print(f"[Memory RAG] Storing {len(self.documents)} documents")
        return self

    def search(self, query: str) -> "MockRAGBuilder":
        """Set the search query."""
        print(f"[Memory RAG] Setting search query: {query}")
        self.search_query = query
        return self

    async def execute(self) -> List[SearchResult]:
        """Execute the search query."""
        print(f"[Memory RAG] Executing search for: {self.search_query}")

        if not self.search_query or not self.documents:
            return []

        # Simulate search based on keyword matching (in a real implementation this would use embeddings)
        results = []
        query_keywords = self.search_query.lower().split()

        for i, doc in enumerate(self.documents):
            # Naive scoring based on keyword presence
            score = 0.0
            for keyword in query_keywords:
                if keyword in doc.lower():
                    score += 0.2

            if score > 0:
                results.append(
                    SearchResult(
                        content=doc,
                        score=min(0.99, score),
                        metadata={"doc_id": i, "length": len(doc)},
                    )
                )

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results


class MockEmbeddingsBuilder:
    """Mock builder for embeddings functionality."""

    def __init__(self, pepper):
        self.pepper = pepper

    def initialize(self) -> None:
        """Initialize the embeddings provider."""
        print("[Hash Embeddings] Initializing provider")


class MockPepperPy:
    """Mock implementation of the PepperPy class."""

    def __init__(self):
        self.initialized = False
        self._rag = None
        self._embeddings = None

    async def __aenter__(self):
        """Context manager entry."""
        print("[PepperPy] Initializing framework")
        self.initialized = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        print("[PepperPy] Cleaning up framework")
        self.initialized = False

    def with_rag(self) -> "MockPepperPy":
        """Add RAG capability."""
        print("[PepperPy] Adding Memory RAG provider")
        self._rag = MockRAGBuilder(self)
        return self

    def with_embeddings(self) -> "MockPepperPy":
        """Add embeddings capability."""
        print("[PepperPy] Adding Hash Embeddings provider")
        self._embeddings = MockEmbeddingsBuilder(self)
        return self

    @property
    def rag(self) -> MockRAGBuilder:
        """Get the RAG builder."""
        if not self._rag:
            raise ValueError("RAG provider not configured. Use with_rag() first.")
        return self._rag

    @property
    def embeddings(self) -> MockEmbeddingsBuilder:
        """Get the embeddings builder."""
        if not self._embeddings:
            raise ValueError(
                "Embeddings provider not configured. Use with_embeddings() first."
            )
        return self._embeddings


async def main() -> None:
    """Run the example."""
    print("In-Memory RAG Provider Example")
    print("==============================\n")

    # Initialize PepperPy with RAG and hash embeddings
    async with MockPepperPy().with_rag().with_embeddings() as pepper:
        # Add some documents
        await pepper.rag.add_documents(
            [
                "The quick brown fox jumps over the lazy dog",
                "The lazy dog sleeps while the quick brown fox jumps",
                "The brown fox is quick and jumps high",
            ]
        )
        await pepper.rag.store()

        # Search the documents
        results = await pepper.rag.search("What does the fox do?").execute()
        print("\nSearch results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.2f} | Content: {result.content}")


if __name__ == "__main__":
    # Note: In the real implementation, these would be required:
    # Required environment variables in .env file:
    # PEPPERPY_RAG__PROVIDER=memory
    # PEPPERPY_EMBEDDINGS__PROVIDER=hash
    asyncio.run(main())
