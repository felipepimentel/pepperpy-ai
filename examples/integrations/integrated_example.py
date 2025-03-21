#!/usr/bin/env python
"""Integrated PepperPy Example.

This example demonstrates how to use multiple PepperPy modules together:
- LLM module for text generation
- RAG module for knowledge retrieval
- Storage module for data persistence
- Core module for configuration and logging

The example shows a practical use case of combining these components
to create a question-answering system with persistent storage.

Requirements:
    - Python 3.9+
    - PepperPy library
    - OpenAI API key

Usage:
    1. Install dependencies:
       poetry install

    2. Set environment variables:
       export OPENAI_API_KEY=your_key_here

    3. Run the example:
       poetry run python examples/integrations/integrated_example.py
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict

from pepperpy.core import validate_config
from pepperpy.llm import LLMProvider
from pepperpy.llm.providers.openai import OpenAIProvider
from pepperpy.rag import RAGProvider
from pepperpy.rag.providers.basic import BasicRAGProvider
from pepperpy.storage import StorageProvider
from pepperpy.storage.providers.local import LocalStorageProvider
from pepperpy.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)


async def setup_environment() -> tuple[LLMProvider, RAGProvider, StorageProvider]:
    """Set up the environment and initialize providers.

    Returns:
        tuple: Initialized LLM, RAG, and Storage providers

    Raises:
        ConfigError: If configuration validation fails
        ValidationError: If API keys are missing
    """
    logger.info("Setting up environment...")

    # Validate environment
    config = {
        "api_keys": {
            "openai": os.environ.get("OPENAI_API_KEY", ""),
        },
        "providers": {
            "llm": "openai",
            "rag": "basic",
            "storage": "local",
        },
    }

    validate_config(config, required=["api_keys.openai"])

    # Initialize providers
    llm_provider = OpenAIProvider(api_key=config["api_keys"]["openai"])
    rag_provider = BasicRAGProvider()
    storage_provider = LocalStorageProvider()

    logger.info("Environment setup complete")
    return llm_provider, rag_provider, storage_provider


async def create_knowledge_base(rag_provider: RAGProvider) -> str:
    """Create and populate a knowledge base.

    Args:
        rag_provider: The RAG provider to use

    Returns:
        str: The name of the created collection
    """
    logger.info("Creating knowledge base...")

    # Create collection
    collection_name = "pepperpy_docs"
    collection = await rag_provider.create_collection(
        name=collection_name,
        description="PepperPy documentation and examples",
    )

    # Add documents
    documents = [
        {
            "content": "PepperPy is a Python framework for building AI applications with a focus on LLMs, RAG, and data management.",
            "metadata": {"source": "docs", "section": "overview"},
        },
        {
            "content": "The LLM module provides a unified interface for working with language models from different providers.",
            "metadata": {"source": "docs", "section": "llm"},
        },
        {
            "content": "The RAG module enables retrieval-augmented generation by combining document retrieval with LLM generation.",
            "metadata": {"source": "docs", "section": "rag"},
        },
        {
            "content": "The Storage module provides persistent storage with support for different backends.",
            "metadata": {"source": "docs", "section": "storage"},
        },
    ]

    for doc in documents:
        await collection.add_document(
            content=doc["content"],
            metadata=doc["metadata"],
        )

    logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
    return collection_name


async def process_query(
    query: str,
    llm_provider: LLMProvider,
    rag_provider: RAGProvider,
    storage_provider: StorageProvider,
    collection_name: str,
) -> Dict[str, Any]:
    """Process a user query using LLM and RAG.

    Args:
        query: The user's question
        llm_provider: Provider for LLM operations
        rag_provider: Provider for RAG operations
        storage_provider: Provider for storage operations
        collection_name: Name of the RAG collection to use

    Returns:
        Dict containing the processing results
    """
    logger.info(f"Processing query: {query}")

    # Generate direct LLM response
    llm_response = await llm_provider.generate(
        prompt=query,
        max_tokens=200,
    )

    # Generate RAG-enhanced response
    rag_response = await rag_provider.generate(
        query=query,
        collection_name=collection_name,
        max_tokens=300,
    )

    # Compare responses
    comparison_prompt = f"""
    Compare these two responses to the query: "{query}"

    Response 1 (Direct LLM):
    {llm_response.text if llm_response.success else "Error: " + str(llm_response.error)}

    Response 2 (RAG-enhanced):
    {rag_response.text if rag_response.success else "Error: " + str(rag_response.error)}

    Analyze how they differ and which is more accurate.
    """

    comparison = await llm_provider.generate(
        prompt=comparison_prompt,
        max_tokens=150,
    )

    # Store results
    result = {
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "llm_response": {
            "text": llm_response.text if llm_response.success else None,
            "error": str(llm_response.error) if not llm_response.success else None,
        },
        "rag_response": {
            "text": rag_response.text if rag_response.success else None,
            "error": str(rag_response.error) if not rag_response.success else None,
        },
        "comparison": {
            "text": comparison.text if comparison.success else None,
            "error": str(comparison.error) if not comparison.success else None,
        },
    }

    # Store in persistent storage
    query_id = f"query_{hash(query) % 10000}"
    await storage_provider.set(query_id, result)

    logger.info(f"Query processing complete. Results stored with ID: {query_id}")
    return result


async def main() -> None:
    """Run the integrated example."""
    try:
        # Initialize providers
        llm_provider, rag_provider, storage_provider = await setup_environment()

        # Create and populate knowledge base
        collection_name = await create_knowledge_base(rag_provider)

        # Process sample query
        sample_query = "How does PepperPy handle different LLM providers?"
        result = await process_query(
            query=sample_query,
            llm_provider=llm_provider,
            rag_provider=rag_provider,
            storage_provider=storage_provider,
            collection_name=collection_name,
        )

        # Display results
        print("\nProcessing Results:")
        print("==================")
        print(f"\nQuery: {result['query']}")
        print(f"Timestamp: {result['timestamp']}")

        print("\nDirect LLM Response:")
        if result["llm_response"]["text"]:
            print(result["llm_response"]["text"])
        else:
            print(f"Error: {result['llm_response']['error']}")

        print("\nRAG-enhanced Response:")
        if result["rag_response"]["text"]:
            print(result["rag_response"]["text"])
        else:
            print(f"Error: {result['rag_response']['error']}")

        print("\nComparison Analysis:")
        if result["comparison"]["text"]:
            print(result["comparison"]["text"])
        else:
            print(f"Error: {result['comparison']['error']}")

    except Exception as e:
        logger.error(f"Error in integrated example: {e}")
        raise


if __name__ == "__main__":
    print("PepperPy Integrated Example")
    print("===========================")
    print("This example demonstrates using multiple PepperPy modules together")
    print("to create a practical question-answering system.\n")

    asyncio.run(main())
