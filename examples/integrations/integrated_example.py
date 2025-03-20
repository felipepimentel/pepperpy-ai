#!/usr/bin/env python
"""Integrated PepperPy Example.

Purpose:
    Demonstrate how to use multiple PepperPy modules together in an integrated application:
    - Using LLM for text generation
    - Using RAG for knowledge retrieval and augmented generation
    - Using Data for persistent storage
    - Combining these components in a cohesive workflow

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
       poetry run python examples/integrated_example.py

IMPORTANT: This is a demonstration of the intended API after refactoring.
Some methods shown here may not be fully implemented yet.
"""

import asyncio
import json
import os
from typing import Any

import pepperpy as pp


async def setup_environment() -> None:
    """Set up the environment for the integrated example.

    Configures PepperPy with default settings and API keys.
    """
    print("Setting up environment...")

    # Configure PepperPy with default settings
    # Note: pp.configure is the intended public API after refactoring
    pp.configure(
        default_llm_provider="openai",
        default_rag_provider="basic",
        default_data_provider="local",
        api_keys={
            "openai": os.environ.get("OPENAI_API_KEY", ""),
        },
    )

    print("Environment setup complete.")


async def create_knowledge_base() -> str:
    """Create a knowledge base for the RAG system.

    Returns:
        str: The name of the created collection
    """
    print("\n=== Creating Knowledge Base ===\n")

    # Create a RAG collection
    collection_name = "pepperpy_knowledge"

    # Note: pp.rag.create_collection is the intended public API after refactoring
    collection = await pp.rag.create_collection(collection_name)

    # Add documents to the collection
    documents = [
        {
            "text": "PepperPy is a Python framework for building AI applications with a focus on LLMs, RAG, and data management.",
            "metadata": {"source": "documentation", "section": "overview"},
        },
        {
            "text": "The LLM module in PepperPy provides a unified interface for working with large language models from different providers.",
            "metadata": {"source": "documentation", "section": "llm"},
        },
        {
            "text": "The RAG module enables retrieval-augmented generation, combining document retrieval with LLM generation.",
            "metadata": {"source": "documentation", "section": "rag"},
        },
        {
            "text": "The Data module provides persistent storage capabilities with support for different backends.",
            "metadata": {"source": "documentation", "section": "data"},
        },
        {
            "text": "PepperPy uses a provider-based architecture with a central registry system for discovering and instantiating providers.",
            "metadata": {"source": "documentation", "section": "architecture"},
        },
    ]

    print(f"Adding {len(documents)} documents to the collection...")

    for doc in documents:
        await collection.add_document(doc["text"], metadata=doc["metadata"])

    print("Knowledge base created successfully.")
    return collection_name


async def create_data_store() -> Any:
    """Create a data store for persistent storage.

    Returns:
        Any: The created data store
    """
    print("\n=== Creating Data Store ===\n")

    # Create a data store
    store_name = "user_queries"

    # Note: pp.data.create_store is the intended public API after refactoring
    store = await pp.data.create_store(store_name)

    print("Data store created successfully.")
    return store


async def process_user_query(query: str, collection_name: str, data_store: Any) -> None:
    """Process a user query using the integrated system.

    Args:
        query: The user's query
        collection_name: The name of the RAG collection to use
        data_store: The data store for persistent storage
    """
    print(f"\n=== Processing Query: '{query}' ===\n")

    # Store the query in the data store
    query_id = f"query_{hash(query) % 10000}"
    await data_store.set(
        query_id,
        {"query": query, "timestamp": "2025-03-11T15:30:00Z", "processed": False},
    )

    # Generate a direct response using LLM
    print("Generating direct LLM response...")
    llm_result = await pp.llm.generate(query)

    if llm_result.success:
        print(f"Direct LLM Response: {llm_result.data}\n")
    else:
        print(f"Error generating direct response: {llm_result.error}\n")

    # Generate a RAG-enhanced response
    print("Generating RAG-enhanced response...")
    rag_result = await pp.rag.generate(query, collection_name=collection_name)

    if rag_result.success:
        print(f"RAG-enhanced Response: {rag_result.data}\n")
    else:
        print(f"Error generating RAG response: {rag_result.error}\n")

    # Compare the responses
    print("Comparing responses...")
    comparison_prompt = f"""
    Compare the following two responses to the query: "{query}"
    
    Response 1 (Direct LLM):
    {llm_result.data if llm_result.success else "Error generating response"}
    
    Response 2 (RAG-enhanced):
    {rag_result.data if rag_result.success else "Error generating response"}
    
    Provide a brief analysis of how the responses differ and which one is better.
    """

    comparison_result = await pp.llm.generate(comparison_prompt)

    if comparison_result.success:
        print(f"Comparison Analysis: {comparison_result.data}\n")
    else:
        print(f"Error generating comparison: {comparison_result.error}\n")

    # Update the query record in the data store
    await data_store.set(
        query_id,
        {
            "query": query,
            "timestamp": "2025-03-11T15:30:00Z",
            "processed": True,
            "direct_response": llm_result.data if llm_result.success else None,
            "rag_response": rag_result.data if rag_result.success else None,
            "comparison": comparison_result.data if comparison_result.success else None,
        },
    )

    print("Query processing complete. Results stored in data store.")


async def main() -> None:
    """Run the integrated example.

    Sets up the environment, creates necessary resources, and processes a sample query.
    """
    # Check for API keys
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if not openai_api_key:
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("This example requires an OpenAI API key to run properly.")
        print("Please set the OPENAI_API_KEY environment variable and try again.")
        return

    try:
        # Setup
        await setup_environment()
        collection_name = await create_knowledge_base()
        data_store = await create_data_store()

        # Process a sample query
        sample_query = "How does PepperPy handle different LLM providers?"
        await process_user_query(sample_query, collection_name, data_store)

        # Retrieve stored data
        print("\n=== Retrieving Stored Data ===\n")
        query_id = f"query_{hash(sample_query) % 10000}"
        stored_data = await data_store.get(query_id)

        if stored_data:
            print("Retrieved stored data:")
            print(json.dumps(stored_data, indent=2))
        else:
            print("No stored data found.")

        print("\nIntegrated example completed successfully.")

    except Exception as e:
        print(f"Error running integrated example: {e}")


if __name__ == "__main__":
    print("PepperPy Integrated Example")
    print("===========================")
    print("This example demonstrates how to use multiple PepperPy modules together.")
    print("Some functionality may not be fully implemented yet.")
    print("This is a demonstration of the API design, not necessarily working code.\n")

    asyncio.run(main())
