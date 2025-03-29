"""
Example demonstrating in-memory RAG capabilities in PepperPy.

This example shows how to use the lightweight in-memory RAG provider
for simple retrieval augmented generation tasks, without requiring
any external dependencies or databases.
"""

import asyncio

from pepperpy import PepperPy


async def main() -> None:
    """Run the example."""
    print("In-Memory RAG Provider Example")
    print("==============================\n")

    # Initialize PepperPy with RAG and embeddings support
    # Provider configuration comes from environment variables
    async with PepperPy().with_rag().with_embeddings() as pepper:
        # Sample documents with metadata
        documents = [
            {
                "text": "Python is a high-level programming language known for its readability and simple syntax.",
                "metadata": {"topic": "programming", "category": "language"},
            },
            {
                "text": "Machine learning is a subset of artificial intelligence focused on building systems that learn from data.",
                "metadata": {"topic": "ai", "category": "concept"},
            },
            {
                "text": "Natural Language Processing (NLP) enables computers to understand and generate human language.",
                "metadata": {"topic": "ai", "category": "nlp"},
            },
            {
                "text": "Python libraries like TensorFlow and PyTorch are commonly used for machine learning tasks.",
                "metadata": {"topic": "programming", "category": "libraries"},
            },
            {
                "text": "Data preprocessing is a crucial step in preparing data for machine learning models.",
                "metadata": {"topic": "ai", "category": "process"},
            },
            {
                "text": "Deep learning models use neural networks with multiple layers to learn representations of data.",
                "metadata": {"topic": "ai", "category": "technique"},
            },
            {
                "text": "Git is a distributed version control system for tracking changes in source code.",
                "metadata": {"topic": "tools", "category": "version control"},
            },
            {
                "text": "Docker containers package code and dependencies together for consistent deployment.",
                "metadata": {"topic": "tools", "category": "containerization"},
            },
            {
                "text": "APIs (Application Programming Interfaces) allow different software systems to communicate.",
                "metadata": {"topic": "programming", "category": "integration"},
            },
            {
                "text": "Cloud computing provides on-demand computing resources over the internet.",
                "metadata": {"topic": "infrastructure", "category": "cloud"},
            },
        ]

        # Add documents with metadata and auto-embeddings
        print("Adding documents...")
        await (
            pepper.rag.add_documents(documents)
            .with_auto_embeddings()  # Let PepperPy handle embeddings
            .store()
        )
        print(f"Added {len(documents)} documents with embeddings")

        # Basic text search
        print("\n1. Basic text search:")
        results = await pepper.rag.search("python programming").limit(3).execute()

        for i, result in enumerate(results, 1):
            print(f"\nResult {i} (score: {result.score:.2f}):")
            print(f"Text: {result.content}")
            print(f"Metadata: {result.metadata}")

        # Vector search with auto embeddings
        print("\n2. Vector search:")
        results = await (
            pepper.rag.search("machine learning and neural networks")
            .with_auto_embeddings()  # Let PepperPy handle embeddings
            .limit(3)
            .execute()
        )

        for i, result in enumerate(results, 1):
            print(f"\nResult {i} (score: {result.score:.2f}):")
            print(f"Text: {result.content}")
            print(f"Metadata: {result.metadata}")

        # Search with metadata filter
        print("\n3. Search with metadata filter:")
        results = await (
            pepper.rag.search("tools")
            .filter({"category": "containerization"})
            .limit(3)
            .execute()
        )

        for i, result in enumerate(results, 1):
            print(f"\nResult {i} (score: {result.score:.2f}):")
            print(f"Text: {result.content}")
            print(f"Metadata: {result.metadata}")

        # List all documents
        print("\n4. All documents in the store:")
        all_docs = await pepper.rag.list_documents()
        print(f"Total documents: {len(all_docs)}")

        # Get stats
        stats = await pepper.rag.get_stats()
        print("\nStats:", stats)

        # Clear the store
        await pepper.rag.clear()
        print("\nMemory cleared")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_RAG__PROVIDER=memory
    # PEPPERPY_EMBEDDINGS__PROVIDER=openai
    # PEPPERPY_EMBEDDINGS__API_KEY=your_api_key
    asyncio.run(main())
