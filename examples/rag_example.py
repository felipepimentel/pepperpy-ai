#!/usr/bin/env python
"""
RAG (Retrieval-Augmented Generation) Example.

This example demonstrates how to use the RAG subsystem 
with a mock implementation.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union


# Mock classes to simulate PepperPy RAG functionality
class Document:
    """Document for RAG system."""

    def __init__(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ):
        self.text = text
        self.metadata = metadata or {}
        self.id = doc_id or f"doc_{hash(text) % 10000}"


class RetrievalResult:
    """Result of RAG retrieval."""

    def __init__(self, document: Document, score: float):
        self.document = document
        self.score = score


class Message:
    """Message for LLM conversations."""

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class MessageRole:
    """Message role constants."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class GenerationResult:
    """Result of text generation."""

    def __init__(self, content: str):
        self.content = content


class MockRAGProvider:
    """Mock RAG provider."""

    def __init__(self, **config):
        self.config = config
        self.initialized = False
        self.documents = {}

        # Bind config to instance attributes
        for key, value in config.items():
            setattr(self, key, value)

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return

        print(f"Initializing RAG provider with config: {self.config}")
        self.initialized = True

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents."""
        if not isinstance(docs, list):
            docs = [docs]

        for doc in docs:
            self.documents[doc.id] = doc
            print(f"Stored document: {doc.id}")

    async def search(
        self, query: str, limit: int = 5, **kwargs
    ) -> List[RetrievalResult]:
        """Search for documents."""
        print(f"Searching for: {query} (limit: {limit})")

        results = []
        for doc in self.documents.values():
            # Simple relevance calculation based on word overlap
            query_words = set(query.lower().split())
            doc_words = set(doc.text.lower().split())
            overlap = query_words.intersection(doc_words)

            if overlap:
                score = len(overlap) / len(query_words)
                results.append(RetrievalResult(doc, score))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def get(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self.documents.get(doc_id)

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        print("Cleaning up RAG provider")
        self.initialized = False


class MockLLMProvider:
    """Mock LLM provider."""

    def __init__(self, **config):
        self.config = config
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return

        print(f"Initializing LLM provider with config: {self.config}")
        self.initialized = True

    async def generate(self, messages: List[Message], **kwargs) -> GenerationResult:
        """Generate text based on messages."""
        # Get the prompt from the last user message
        last_message = next(
            (m for m in reversed(messages) if m.role == MessageRole.USER), None
        )
        if not last_message:
            return GenerationResult("No user message found.")

        # Process context information if present
        context = None
        for message in messages:
            if message.role == MessageRole.SYSTEM and "Context:" in message.content:
                context = message.content

        if context:
            return GenerationResult(
                f"Based on the provided context, I can answer about '{last_message.content}'."
            )
        else:
            return GenerationResult(
                f"I don't have enough information to answer about '{last_message.content}'."
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        print("Cleaning up LLM provider")
        self.initialized = False


async def basic_rag_example():
    """Basic RAG example."""
    print("\n=== Basic RAG Example ===")

    # Create RAG provider
    rag_provider = MockRAGProvider(
        embedding_provider="openai",
        chunk_size=1000,
        chunk_overlap=100,
    )

    # Initialize provider
    await rag_provider.initialize()

    try:
        # Store sample documents
        print("\n--- Storing Documents ---")
        docs = [
            Document(
                text="Python is a high-level programming language known for its readability and versatility.",
                metadata={"source": "wiki", "date": "2023-01-01"},
            ),
            Document(
                text="PepperPy is a Python framework for building AI applications with a unified interface.",
                metadata={"source": "docs", "date": "2023-04-15"},
            ),
            Document(
                text="Retrieval-Augmented Generation (RAG) combines retrieval and generation for more accurate results.",
                metadata={"source": "research", "date": "2023-02-10"},
            ),
            Document(
                text="Large language models (LLMs) are neural networks trained on massive text datasets.",
                metadata={"source": "textbook", "date": "2023-03-20"},
            ),
        ]

        await rag_provider.store(docs)

        # Search for documents
        print("\n--- Searching ---")
        query = "What is PepperPy framework?"
        print(f"Query: {query}")

        results = await rag_provider.search(query, limit=2)

        print("\n--- Results ---")
        for i, result in enumerate(results):
            print(f"\nResult {i+1} (Score: {result.score:.2f})")
            print(f"Text: {result.document.text}")
            print(f"Metadata: {result.document.metadata}")

    finally:
        # Clean up
        await rag_provider.cleanup()


async def rag_with_llm_example():
    """RAG with LLM integration example."""
    print("\n=== RAG with LLM Integration ===")

    # Create providers
    rag_provider = MockRAGProvider(embedding_provider="openai")
    llm_provider = MockLLMProvider(model="gpt-4")

    # Initialize providers
    await rag_provider.initialize()
    await llm_provider.initialize()

    try:
        # Store sample documents
        docs = [
            Document(
                text="PepperPy is a flexible framework for AI applications, designed to be modular and extensible.",
                metadata={"source": "docs", "section": "overview"},
            ),
            Document(
                text="PepperPy plugins follow a provider pattern with common lifecycle methods like initialize and cleanup.",
                metadata={"source": "docs", "section": "plugins"},
            ),
        ]

        await rag_provider.store(docs)

        # Perform RAG search
        query = "How does PepperPy plugin system work?"
        results = await rag_provider.search(query)

        if results:
            # Create context from retrieved documents
            context = "Context:\n"
            for i, result in enumerate(results):
                context += f"{i+1}. {result.document.text}\n"

            # Create messages with context
            messages = [
                Message(role=MessageRole.SYSTEM, content=context),
                Message(role=MessageRole.USER, content=query),
            ]

            # Generate response using LLM
            print("\n--- RAG-enhanced Generation ---")
            print(f"Query: {query}")
            print(f"Number of relevant documents found: {len(results)}")

            response = await llm_provider.generate(messages)
            print(f"\nResponse: {response.content}")
        else:
            print(f"No relevant documents found for: {query}")

    finally:
        # Clean up
        await rag_provider.cleanup()
        await llm_provider.cleanup()


async def main():
    """Run the example."""
    print("=== PepperPy RAG Examples ===")

    await basic_rag_example()
    await rag_with_llm_example()

    print("\nRAG examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
