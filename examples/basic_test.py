"""
Basic test script to verify the functionality of the refactored PepperPy modules.

This script imports and uses various modules from the PepperPy framework
to ensure they are working correctly after the refactoring.
"""

import asyncio
import json
import os
from typing import Any, Dict

from pepperpy.errors import PepperPyError
from pepperpy.storage import MemoryStorage, Storage
from pepperpy.workflows import Workflow, WorkflowContext, WorkflowStep


async def test_storage():
    """Test the storage module."""
    print("\n=== Testing Storage Module ===")

    # Create a memory storage provider
    storage_provider = MemoryStorage()
    storage = Storage(storage_provider)

    # Save some data
    storage.save("test_key", {"name": "Test Data", "value": 42})
    print("Saved data to storage")

    # Load the data
    data = storage.load("test_key")
    print(f"Loaded data from storage: {data}")

    # List all keys
    keys = storage.list()
    print(f"Storage keys: {keys}")

    # Delete the data
    storage.delete("test_key")
    print("Deleted data from storage")

    # Verify it's gone
    data = storage.load("test_key")
    print(f"Data after deletion: {data}")

    return True


async def process_data(data: Any, context: WorkflowContext) -> Dict[str, Any]:
    """Process data in a workflow step."""
    print(f"Processing data: {data}")
    return {"processed": data, "timestamp": "2023-01-01"}


async def test_workflows():
    """Test the workflows module."""
    print("\n=== Testing Workflows Module ===")

    # Create a workflow with a properly awaited function
    workflow = Workflow("test_workflow", "A test workflow")

    # Define a synchronous function for the workflow step
    def sync_process_data(data: Any, context: WorkflowContext) -> Dict[str, Any]:
        print(f"Processing data: {data}")
        return {"processed": data, "timestamp": "2023-01-01"}

    # Add steps
    step1 = WorkflowStep(
        name="step1",
        func=sync_process_data,
        input_key="input_data",
        output_key="processed_data",
    )
    workflow.add_step(step1)

    # Create a context
    context = WorkflowContext({"input_data": "Hello, World!"})

    # Execute the workflow
    result_context = await workflow.execute(context)

    # Check the results
    print(f"Workflow results: {result_context.results}")
    print(f"Workflow context data: {result_context.data}")

    return True


async def test_config():
    """Test the config module."""
    print("\n=== Testing Config Module ===")

    # Create a test config file
    config_content = {
        "app": {"name": "TestApp", "version": "1.0.0"},
        "database": {
            "host": "localhost",
            "port": 5432,
            "username": "test_user",
            "password": "test_password",
        },
    }

    with open("test_config.json", "w") as f:
        json.dump(config_content, f, indent=2)

    # Load the config
    with open("test_config.json", "r") as f:
        config = json.load(f)
    print(f"Loaded config: {config}")

    # Clean up
    os.remove("test_config.json")

    return True


async def test_errors():
    """Test the errors module."""
    print("\n=== Testing Errors Module ===")

    try:
        # Raise a PepperPy error
        raise PepperPyError("This is a test error", code=42, source="test_script")
    except PepperPyError as e:
        print(f"Caught error: {e}")
        print(f"Error metadata: {e.metadata}")

    return True


async def main():
    """Run all tests."""
    tests = [
        test_storage,
        test_workflows,
        test_config,
        test_errors,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"Error in {test.__name__}: {e}")
            results.append((test.__name__, False))

    # Print summary
    print("\n=== Test Summary ===")
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
