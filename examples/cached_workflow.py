"""Example of using workflow caching.

This example demonstrates how to use the WorkflowCache class to efficiently
execute workflow steps by caching results.
"""

import asyncio
import time
from typing import Any, Dict

from pepperpy.workflows.base import WorkflowStep
from pepperpy.workflows.core.cache import WorkflowCache


async def expensive_computation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate an expensive computation.

    Args:
        data: Input data

    Returns:
        Processed data
    """
    print(f"Running expensive computation on {data}")
    # Simulate work
    await asyncio.sleep(2)
    return {"result": data["value"] * 2}


async def main():
    """Run the cached workflow example."""
    # Create a workflow cache
    workflow_cache = WorkflowCache(namespace="example_workflow")

    # Create some workflow steps
    step1 = WorkflowStep(
        name="process_data",
        description="Process input data",
        action="data_transformation",
    )

    step2 = WorkflowStep(
        name="analyze_data",
        description="Analyze processed data",
        action="data_analysis",
    )

    # Example parameters
    params1 = {"value": 42}
    params2 = {"value": 100}

    # First run - should compute and cache results
    print("First run - computing and caching results:")

    start_time = time.time()

    # Check cache for step1 with params1
    result1 = await workflow_cache.get_step_result(step1, params1)
    if result1 is None:
        print("Cache miss for step1 with params1")
        result1 = await expensive_computation(params1)
        await workflow_cache.set_step_result(step1, params1, result1)
    else:
        print("Cache hit for step1 with params1")

    # Check cache for step1 with params2
    result2 = await workflow_cache.get_step_result(step1, params2)
    if result2 is None:
        print("Cache miss for step1 with params2")
        result2 = await expensive_computation(params2)
        await workflow_cache.set_step_result(step1, params2, result2)
    else:
        print("Cache hit for step1 with params2")

    end_time = time.time()
    print(f"First run completed in {end_time - start_time:.4f} seconds")
    print(f"Results: {result1}, {result2}")

    # Second run - should use cached results
    print("\nSecond run - using cached results:")

    start_time = time.time()

    # Check cache for step1 with params1
    result1 = await workflow_cache.get_step_result(step1, params1)
    if result1 is None:
        print("Cache miss for step1 with params1")
        result1 = await expensive_computation(params1)
        await workflow_cache.set_step_result(step1, params1, result1)
    else:
        print("Cache hit for step1 with params1")

    # Check cache for step1 with params2
    result2 = await workflow_cache.get_step_result(step1, params2)
    if result2 is None:
        print("Cache miss for step1 with params2")
        result2 = await expensive_computation(params2)
        await workflow_cache.set_step_result(step1, params2, result2)
    else:
        print("Cache hit for step1 with params2")

    end_time = time.time()
    print(f"Second run completed in {end_time - start_time:.4f} seconds")
    print(f"Results: {result1}, {result2}")

    # Invalidate one of the cached results
    print("\nInvalidating cache for params1:")
    await workflow_cache.invalidate_step(step1, params1)

    # Third run - should use cache for params2 but recompute for params1
    print("\nThird run - mixed cache hits and misses:")

    start_time = time.time()

    # Check cache for step1 with params1
    result1 = await workflow_cache.get_step_result(step1, params1)
    if result1 is None:
        print("Cache miss for step1 with params1")
        result1 = await expensive_computation(params1)
        await workflow_cache.set_step_result(step1, params1, result1)
    else:
        print("Cache hit for step1 with params1")

    # Check cache for step1 with params2
    result2 = await workflow_cache.get_step_result(step1, params2)
    if result2 is None:
        print("Cache miss for step1 with params2")
        result2 = await expensive_computation(params2)
        await workflow_cache.set_step_result(step1, params2, result2)
    else:
        print("Cache hit for step1 with params2")

    end_time = time.time()
    print(f"Third run completed in {end_time - start_time:.4f} seconds")
    print(f"Results: {result1}, {result2}")

    # Clean up
    await workflow_cache.clear()


if __name__ == "__main__":
    asyncio.run(main())
