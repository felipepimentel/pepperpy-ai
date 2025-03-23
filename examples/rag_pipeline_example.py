"""Example demonstrating the usage of the RAG pipeline system in PepperPy."""

import asyncio

from pepperpy.rag import Document, Query
from pepperpy.rag.pipeline import (
    ChunkingStage,
    EmbeddingStage,
    RAGPipeline,
    RerankingStage,
    RetrievalStage,
)


async def run_example() -> None:
    """Run the RAG pipeline example."""
    # Create documents
    documents = [
        Document(
            id="doc1",
            content="""
            Machine learning is a subset of artificial intelligence that focuses on
            developing systems that can learn from and make decisions based on data.
            Common types of machine learning include supervised learning,
            unsupervised learning, and reinforcement learning.

            Supervised learning involves training models on labeled data, where the
            desired output is known. For example, training a model to classify
            images of cats and dogs using a dataset of labeled images.

            Unsupervised learning works with unlabeled data to discover hidden
            patterns or groupings. Clustering algorithms are a common example,
            where the model groups similar data points together without prior
            knowledge of the categories.
            """,
            metadata={"topic": "machine_learning", "type": "overview"},
        ),
        Document(
            id="doc2",
            content="""
            Deep learning is a specialized form of machine learning that uses
            artificial neural networks with multiple layers (deep neural networks).
            These networks are inspired by the structure and function of the
            human brain.

            Neural networks consist of layers of interconnected nodes or "neurons"
            that process and transform input data. Each connection has a weight
            that is adjusted during training to minimize prediction errors.

            Common applications of deep learning include:
            - Image and speech recognition
            - Natural language processing
            - Autonomous vehicles
            - Game playing AI
            """,
            metadata={"topic": "deep_learning", "type": "overview"},
        ),
    ]

    # Create pipeline stages
    stages = [
        ChunkingStage(chunk_size=200, chunk_overlap=50),  # Split into smaller chunks
        EmbeddingStage(),  # Generate embeddings
        RetrievalStage(),  # Retrieve relevant chunks
        RerankingStage(),  # Rerank results by relevance
    ]

    # Initialize pipeline
    pipeline = RAGPipeline(stages=stages)

    # Create query
    query = Query(
        text="What are the main types of machine learning?",
        metadata={"topic": "machine_learning"},
    )

    # Process documents through pipeline
    result = await pipeline.process(documents, query=query)

    # Print results
    print("\nQuery:", query.text)
    print("\nRelevant Document Chunks:")
    print("-" * 50)
    for doc, score in zip(result.documents, result.scores):
        print(f"\nScore: {score:.3f}")
        print("Content:", doc.content.strip())
        print("Metadata:", doc.metadata)
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(run_example())
