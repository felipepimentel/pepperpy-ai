#!/usr/bin/env python
"""RAG Providers Example using PepperPy.

Purpose:
    Demonstrate how to use different RAG (Retrieval Augmented Generation) providers
    in the refactored PepperPy library, including:
    - Creating and managing collections
    - Adding documents to collections
    - Querying collections
    - Generating responses with context
    - Working with different provider-specific parameters

Requirements:
    - Python 3.9+
    - PepperPy library
    - API keys for the providers you want to use

Usage:
    1. Install dependencies:
       poetry install

    2. Set environment variables:
       export OPENAI_API_KEY=your_openai_api_key
       export PINECONE_API_KEY=your_pinecone_api_key (optional)
       # Or use .env file (see .env.example)

    3. Run the example:
       poetry run python examples/rag_providers.py

IMPORTANT: This is a demonstration of the intended API after refactoring.
Some methods shown here may not be fully implemented yet.
"""

import asyncio
import logging
import os

# Import utility functions
from utils import check_api_keys, load_env, setup_logging

import pepperpy as pp

# Set up logger
logger = logging.getLogger(__name__)


async def basic_rag_example() -> None:
    """Example of using the basic RAG provider.

    Demonstrates how to:
    - Create a collection
    - Add documents to the collection
    - Query the collection
    - Generate responses with context

    Note: This demonstrates the intended API pattern after refactoring.
    """
    logger.info("Running basic RAG example")
    print("\n=== Basic RAG Example ===\n")

    # Create a collection
    print("Creating a collection...")
    logger.info("Creating a collection")

    # Note: pp.rag.create_collection is the intended public API after refactoring
    collection = await pp.rag.create_collection(
        name="example_docs",
        provider="basic",
        embedding_model="openai:text-embedding-3-small",
    )

    # Add documents to the collection
    documents = [
        {
            "id": "doc1",
            "text": """
            PepperPy is a Python framework for building AI applications.
            It provides a unified interface for working with different LLM providers,
            RAG systems, and data storage solutions.
            """,
            "metadata": {"source": "documentation", "section": "overview"},
        },
        {
            "id": "doc2",
            "text": """
            Retrieval Augmented Generation (RAG) is a technique that enhances
            LLM responses by retrieving relevant information from a knowledge base
            before generating a response.
            """,
            "metadata": {"source": "documentation", "section": "rag"},
        },
        {
            "id": "doc3",
            "text": """
            PepperPy supports multiple LLM providers including OpenAI, Anthropic,
            and custom REST-based providers. This allows you to switch between
            different models without changing your application code.
            """,
            "metadata": {"source": "documentation", "section": "llm"},
        },
    ]

    print("Adding documents to the collection...")
    logger.info("Adding documents to the collection")

    # Note: collection.add_documents is the intended API after refactoring
    await collection.add_documents(documents)

    # Query the collection
    query = "What is RAG and how does it work?"
    print(f"Querying the collection with: '{query}'")
    logger.info(f"Querying the collection with: '{query}'")

    # Note: collection.query is the intended API after refactoring
    results = await collection.query(
        query=query,
        top_k=2,
    )

    print("\nQuery results:")
    for i, result in enumerate(results):
        print(f"Result {i + 1}:")
        print(f"  Score: {result.score}")
        print(f"  Document ID: {result.document_id}")
        print(f"  Text: {result.text[:100]}...")
        print(f"  Metadata: {result.metadata}")
        print()

    # Generate a response with context
    print("Generating a response with context...")
    logger.info("Generating a response with context")

    # Note: pp.rag.generate is the intended API after refactoring
    response = await pp.rag.generate(
        query=query,
        collection=collection,
        llm_provider="openai",
        llm_model="gpt-4o",
    )

    print("\nGenerated response:")
    print(response.text)


async def vector_store_example() -> None:
    """Example of using a vector store RAG provider.

    Demonstrates how to:
    - Create a collection with a vector store provider
    - Add documents to the collection
    - Query the collection with different parameters
    - Delete documents from the collection

    Note: This demonstrates the intended API pattern after refactoring.
    """
    logger.info("Running vector store example")
    print("\n=== Vector Store Example ===\n")

    # Create a collection with a vector store provider
    print("Creating a collection with vector store provider...")
    logger.info("Creating a collection with vector store provider")

    # Note: pp.rag.create_collection is the intended public API after refactoring
    collection = await pp.rag.create_collection(
        name="vector_store_docs",
        provider="pinecone",  # Example vector store provider
        embedding_model="openai:text-embedding-3-small",
        index_name="pepperpy-example",
        namespace="examples",
    )

    # Add documents to the collection
    documents = [
        {
            "id": "vs1",
            "text": """
            Vector databases are specialized databases designed to store and
            search vector embeddings efficiently. They are commonly used in
            RAG systems to store document embeddings and perform similarity searches.
            """,
            "metadata": {"category": "databases", "level": "intermediate"},
        },
        {
            "id": "vs2",
            "text": """
            Embeddings are numerical representations of text, images, or other data
            that capture semantic meaning. In NLP, embeddings map words or documents
            to vectors in a high-dimensional space where similar items are closer together.
            """,
            "metadata": {"category": "nlp", "level": "beginner"},
        },
        {
            "id": "vs3",
            "text": """
            Similarity search finds items in a dataset that are most similar to a query.
            In vector databases, this is typically done using metrics like cosine similarity
            or Euclidean distance between vector embeddings.
            """,
            "metadata": {"category": "search", "level": "intermediate"},
        },
    ]

    print("Adding documents to the vector store collection...")
    logger.info("Adding documents to the vector store collection")

    # Note: collection.add_documents is the intended API after refactoring
    await collection.add_documents(documents)

    # Query the collection with different parameters
    query = "How do vector databases work with embeddings?"
    print(f"Querying the vector store with: '{query}'")
    logger.info(f"Querying the vector store with: '{query}'")

    # Note: collection.query is the intended API after refactoring
    results = await collection.query(
        query=query,
        top_k=2,
        filter={"level": "intermediate"},  # Metadata filtering
    )

    print("\nQuery results with filtering:")
    for i, result in enumerate(results):
        print(f"Result {i + 1}:")
        print(f"  Score: {result.score}")
        print(f"  Document ID: {result.document_id}")
        print(f"  Text: {result.text[:100]}...")
        print(f"  Metadata: {result.metadata}")
        print()

    # Delete a document
    print("Deleting a document from the collection...")
    logger.info("Deleting a document from the collection")

    # Note: collection.delete_documents is the intended API after refactoring
    await collection.delete_documents(["vs1"])

    # Query again to verify deletion
    print("Querying again after deletion...")
    logger.info("Querying again after deletion")

    results = await collection.query(
        query=query,
        top_k=3,  # Request more results to see what's available
    )

    print("\nQuery results after deletion:")
    for i, result in enumerate(results):
        print(f"Result {i + 1}:")
        print(f"  Document ID: {result.document_id}")
        print(f"  Text: {result.text[:100]}...")
        print()


async def hybrid_search_example() -> None:
    """Example of using hybrid search with a RAG provider.

    Demonstrates how to:
    - Configure a RAG provider with hybrid search capabilities
    - Create a collection with hybrid search settings
    - Query using both semantic and keyword search

    Note: This demonstrates the intended API pattern after refactoring.
    """
    logger.info("Running hybrid search example")
    print("\n=== Hybrid Search Example ===\n")

    # Configure RAG with hybrid search settings
    print("Configuring RAG with hybrid search settings...")
    logger.info("Configuring RAG with hybrid search settings")

    # Note: pp.rag.configure is the intended public API after refactoring
    pp.rag.configure(
        provider="hybrid",
        embedding_model="openai:text-embedding-3-small",
        semantic_weight=0.7,  # 70% semantic search, 30% keyword search
        keyword_search_method="bm25",
    )

    # Create a collection with hybrid search
    print("Creating a collection with hybrid search...")
    logger.info("Creating a collection with hybrid search")

    # Note: pp.rag.create_collection is the intended public API after refactoring
    collection = await pp.rag.create_collection(
        name="hybrid_search_docs",
        provider="hybrid",
    )

    # Add documents to the collection
    documents = [
        {
            "id": "h1",
            "text": """
            Hybrid search combines multiple search techniques to improve results.
            It typically uses both semantic search (based on embeddings) and
            keyword search (based on exact matches) to find relevant documents.
            """,
            "metadata": {"topic": "search"},
        },
        {
            "id": "h2",
            "text": """
            BM25 (Best Matching 25) is a ranking function used in information retrieval.
            It's based on the probabilistic retrieval framework and is commonly used
            for keyword-based document ranking in search engines.
            """,
            "metadata": {"topic": "algorithms"},
        },
        {
            "id": "h3",
            "text": """
            Semantic search uses understanding of natural language to find relevant results.
            Unlike keyword search, it can find documents that share meaning even if they
            don't contain the exact search terms.
            """,
            "metadata": {"topic": "search"},
        },
    ]

    print("Adding documents to the hybrid search collection...")
    logger.info("Adding documents to the hybrid search collection")

    # Note: collection.add_documents is the intended API after refactoring
    await collection.add_documents(documents)

    # Query using hybrid search
    query = "How does BM25 algorithm work?"
    print(f"Querying with hybrid search: '{query}'")
    logger.info(f"Querying with hybrid search: '{query}'")

    # Note: collection.query is the intended API after refactoring
    results = await collection.query(
        query=query,
        top_k=2,
        semantic_weight=0.5,  # Override the default weight for this query
    )

    print("\nHybrid search results:")
    for i, result in enumerate(results):
        print(f"Result {i + 1}:")
        print(f"  Score: {result.score}")
        print(f"  Document ID: {result.document_id}")
        print(f"  Text: {result.text[:100]}...")
        print()


async def main() -> None:
    """Run the RAG provider examples.

    Runs examples for different RAG providers, including basic RAG,
    vector store, and hybrid search.
    """
    # Load environment variables from .env file
    load_env()

    # Set up logging
    setup_logging()

    # Check for required API keys
    required_keys = {"OPENAI_API_KEY": "All examples (for embeddings)"}
    optional_keys = {"PINECONE_API_KEY": "Vector store example"}
    check_api_keys(required_keys, optional_keys)

    logger.info("Starting RAG provider examples")

    try:
        # Run examples
        await basic_rag_example()

        # Only run vector store example if PINECONE_API_KEY is available
        if "PINECONE_API_KEY" in os.environ:
            await vector_store_example()
        else:
            print("\nSkipping vector store example due to missing PINECONE_API_KEY")
            logger.warning(
                "Skipping vector store example due to missing PINECONE_API_KEY"
            )

        await hybrid_search_example()

        logger.info("RAG provider examples completed successfully")
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    print("PepperPy RAG Providers Usage Examples")
    print("====================================")
    print("This example demonstrates the intended usage patterns after refactoring.")
    print("Some functionality may not be fully implemented yet.")
    print("This is a demonstration of the API design, not necessarily working code.")

    asyncio.run(main())
