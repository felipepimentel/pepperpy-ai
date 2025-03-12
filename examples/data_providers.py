#!/usr/bin/env python
"""Data Storage Example using PepperPy.

Purpose:
    Demonstrate how to use the Data storage functionality in the refactored PepperPy library, including:
    - Creating and managing data stores
    - Storing and retrieving data
    - Working with metadata and TTL (Time To Live)
    - Performing batch operations
    - Configuring data providers with custom settings

Requirements:
    - Python 3.9+
    - PepperPy library
    - Redis (optional, for advanced examples)

Usage:
    1. Install dependencies:
       poetry install

    2. Set environment variables (optional):
       export REDIS_CONNECTION_STRING=redis://localhost:6379
       # Or use .env file (see .env.example)

    3. Run the example:
       poetry run python examples/data_providers.py

IMPORTANT: This is a demonstration of the intended API after refactoring.
Some methods shown here may not be fully implemented yet.
"""

import asyncio
import json
import logging
import os

# Import utility functions
from utils import load_env, setup_logging

import pepperpy as pp

# Set up logger
logger = logging.getLogger(__name__)


async def basic_data_example() -> None:
    """Example of using the basic Data functionality.

    Demonstrates the core data operations:
    - Creating a data store
    - Setting data
    - Getting data
    - Checking if keys exist
    - Deleting data

    Note: This demonstrates the intended API pattern after refactoring.
    """
    logger.info("Running basic data example")
    print("\n=== Basic Data Example ===\n")

    # Create a data store
    print("Creating a data store...")
    logger.info("Creating a data store")

    # Note: pp.data.create_store is the intended public API after refactoring
    store = await pp.data.create_store("example_store")

    # Add data to the store
    data = {
        "name": "PepperPy",
        "version": "1.0.0",
        "description": "A Python framework for building AI applications",
        "features": [
            "LLM integration",
            "RAG capabilities",
            "Data storage",
            "Workflow management",
        ],
    }

    print("Adding data to the store...")
    logger.info("Adding data to the store")

    # Note: store.set is the intended API after refactoring
    await store.set("project_info", data)

    # Get data from the store
    print("Retrieving data from the store...")
    logger.info("Retrieving data from the store")

    # Note: store.get is the intended API after refactoring
    result = await store.get("project_info")

    if result:
        print("Retrieved data:")
        print(json.dumps(result, indent=2))
    else:
        print("No data found")
        logger.warning("No data found")

    # Check if a key exists
    key = "project_info"
    print(f"\nChecking if key '{key}' exists...")
    logger.info(f"Checking if key '{key}' exists")

    # Note: store.exists is the intended API after refactoring
    exists = await store.exists(key)

    print(f"Key '{key}' exists: {exists}")

    # Delete data
    print(f"\nDeleting key '{key}'...")
    logger.info(f"Deleting key '{key}'")

    # Note: store.delete is the intended API after refactoring
    await store.delete(key)

    # Verify deletion
    exists = await store.exists(key)
    print(f"Key '{key}' exists after deletion: {exists}")
    logger.info(f"Key '{key}' exists after deletion: {exists}")


async def advanced_data_example() -> None:
    """Example of using advanced Data features.

    Demonstrates advanced data capabilities:
    - Configuring data providers with custom settings
    - Creating stores with custom parameters
    - Setting data with expiration (TTL)
    - Getting data with default values
    - Performing batch operations

    Note: This demonstrates the intended API pattern after refactoring.
    """
    logger.info("Running advanced data example")
    print("\n=== Advanced Data Example ===\n")

    # Configure Data with custom settings
    print("Configuring Data with custom settings...")
    logger.info("Configuring Data with custom settings")

    # Get connection string from environment variables
    connection_string = os.environ.get(
        "REDIS_CONNECTION_STRING", "redis://localhost:6379"
    )
    ttl = int(os.environ.get("DEFAULT_TTL", "3600"))  # Default 1 hour

    # Note: pp.data.configure is the intended public API after refactoring
    pp.data.configure(
        default_provider="redis",
        connection_string=connection_string,
        ttl=ttl,
    )

    # Create a store with custom settings
    print("Creating a store with custom settings...")
    logger.info("Creating a store with custom settings")

    # Note: pp.data.create_store with custom settings is the intended API
    store = await pp.data.create_store(
        name="advanced_store",
        provider="redis",
        ttl=7200,  # 2 hours
        namespace="pepperpy:example",
    )

    # Add data with expiration
    data = {
        "session_id": "abc123",
        "user": "example_user",
        "created_at": "2025-03-11T12:00:00Z",
        "data": {"key1": "value1", "key2": "value2"},
    }

    print("Adding data with custom TTL...")
    logger.info("Adding data with custom TTL")

    # Note: store.set with TTL is the intended API
    await store.set("session_data", data, ttl=300)  # 5 minutes

    # Get data with default value
    print("Retrieving data with default value...")
    logger.info("Retrieving data with default value")

    # Note: store.get with default is the intended API
    result = await store.get("non_existent_key", default={"status": "not_found"})

    print("Retrieved data (with default):")
    print(json.dumps(result, indent=2))

    # Batch operations
    print("\nPerforming batch operations...")
    logger.info("Performing batch operations")

    # Note: batch operations are the intended API
    batch_data = {
        "key1": {"value": "data1"},
        "key2": {"value": "data2"},
        "key3": {"value": "data3"},
    }

    # Batch set
    print("Batch set operation...")
    logger.info("Performing batch set operation")
    await store.batch_set(batch_data)

    # Batch get
    print("Batch get operation...")
    logger.info("Performing batch get operation")
    keys = ["key1", "key2", "key3", "key4"]
    results = await store.batch_get(keys)

    print("Batch get results:")
    for key, value in results.items():
        print(f"  {key}: {value}")

    # Batch delete
    print("\nBatch delete operation...")
    logger.info("Performing batch delete operation")
    delete_keys = ["key1", "key2"]
    await store.batch_delete(delete_keys)

    # Verify deletion
    results = await store.batch_get(keys)
    print("After batch delete:")
    for key, value in results.items():
        print(f"  {key}: {value}")


async def main() -> None:
    """Run the Data storage examples.

    Runs the basic and advanced data storage examples.
    """
    # Load environment variables from .env file
    load_env()

    # Set up logging
    setup_logging()

    logger.info("Starting Data storage examples")

    try:
        # Run examples
        await basic_data_example()
        await advanced_data_example()

        logger.info("Data storage examples completed successfully")
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    print("PepperPy Data Module Usage Examples")
    print("==================================")
    print("This example demonstrates the intended usage patterns after refactoring.")
    print("Some functionality may not be fully implemented yet.")
    print("This is a demonstration of the API design, not necessarily working code.")

    asyncio.run(main())
