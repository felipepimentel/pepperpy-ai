#!/usr/bin/env python
"""Example demonstrating the use of context managers for resource management.

This example demonstrates the use of various context managers provided by
the PepperPy framework for resource management, including resource pools,
timed contexts, and retry contexts.
"""

import asyncio
import random
import time
from typing import List

from pepperpy.core.context import (
    AsyncPooledResourceManager,
    AsyncRetryContext,
    AsyncTimedContext,
    PooledResourceManager,
    RetryContext,
    TimedContext,
    async_retry,
    async_timed,
    resource_context,
    retry,
    timed,
)
from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


class Resource:
    """A simple resource class for demonstration purposes."""

    def __init__(self, resource_id: int):
        """Initialize the resource.

        Args:
            resource_id: The ID of the resource
        """
        self.resource_id = resource_id
        self.in_use = False
        logger.info(f"Resource {resource_id} created")

    def use(self) -> None:
        """Use the resource."""
        if self.in_use:
            raise PepperpyError(f"Resource {self.resource_id} is already in use")
        self.in_use = True
        logger.info(f"Resource {self.resource_id} is now in use")

    def release(self) -> None:
        """Release the resource."""
        if not self.in_use:
            raise PepperpyError(f"Resource {self.resource_id} is not in use")
        self.in_use = False
        logger.info(f"Resource {self.resource_id} has been released")

    def close(self) -> None:
        """Close the resource."""
        logger.info(f"Resource {self.resource_id} has been closed")

    def __str__(self) -> str:
        """Get a string representation of the resource.

        Returns:
            A string representation of the resource
        """
        return f"Resource({self.resource_id}, in_use={self.in_use})"


class AsyncResource:
    """A simple asynchronous resource class for demonstration purposes."""

    def __init__(self, resource_id: int):
        """Initialize the resource.

        Args:
            resource_id: The ID of the resource
        """
        self.resource_id = resource_id
        self.in_use = False
        logger.info(f"AsyncResource {resource_id} created")

    async def use(self) -> None:
        """Use the resource asynchronously."""
        if self.in_use:
            raise PepperpyError(f"AsyncResource {self.resource_id} is already in use")
        self.in_use = True
        await asyncio.sleep(0.1)  # Simulate some async work
        logger.info(f"AsyncResource {self.resource_id} is now in use")

    async def release(self) -> None:
        """Release the resource asynchronously."""
        if not self.in_use:
            raise PepperpyError(f"AsyncResource {self.resource_id} is not in use")
        self.in_use = False
        await asyncio.sleep(0.1)  # Simulate some async work
        logger.info(f"AsyncResource {self.resource_id} has been released")

    async def close(self) -> None:
        """Close the resource asynchronously."""
        await asyncio.sleep(0.1)  # Simulate some async work
        logger.info(f"AsyncResource {self.resource_id} has been closed")

    def __str__(self) -> str:
        """Get a string representation of the resource.

        Returns:
            A string representation of the resource
        """
        return f"AsyncResource({self.resource_id}, in_use={self.in_use})"


class ResourceManager:
    """A simple resource manager for demonstration purposes."""

    def __init__(self):
        """Initialize the resource manager."""
        self.next_id = 1
        self.resources: List[Resource] = []

    def create_resource(self) -> Resource:
        """Create a new resource.

        Returns:
            The created resource
        """
        resource = Resource(self.next_id)
        self.next_id += 1
        self.resources.append(resource)
        return resource

    def acquire_resource(self) -> Resource:
        """Acquire a resource.

        Returns:
            The acquired resource
        """
        resource = self.create_resource()
        resource.use()
        return resource

    def release_resource(self, resource: Resource) -> None:
        """Release a resource.

        Args:
            resource: The resource to release
        """
        resource.release()


def example_resource_manager() -> None:
    """Example demonstrating the use of a resource manager."""
    print("\n=== Resource Manager Example ===")

    # Create a resource manager
    manager = ResourceManager()

    # Use a resource with a context manager
    with resource_context(
        manager.acquire_resource, manager.release_resource
    ) as resource:
        print(f"Using {resource}")
        # Do something with the resource
        time.sleep(0.1)

    print("Resource has been automatically released")


def example_pooled_resource_manager() -> None:
    """Example demonstrating the use of a pooled resource manager."""
    print("\n=== Pooled Resource Manager Example ===")

    # Create a factory function for resources
    resource_id = 0

    def create_resource() -> Resource:
        nonlocal resource_id
        resource_id += 1
        return Resource(resource_id)

    # Create a pooled resource manager
    pool = PooledResourceManager(
        name="resource-pool",
        factory=create_resource,
        max_size=3,
        min_size=1,
        timeout=2.0,
    )

    # Add some metadata to the pool
    pool.with_metadata("created_at", time.time())
    pool.with_metadata("purpose", "example")

    # Use resources from the pool
    resources = []
    for _ in range(3):
        with pool as resource:
            print(f"Using {resource} from pool {pool.name}")
            resources.append(resource)
            # Do something with the resource
            time.sleep(0.1)

    print(f"Pool metadata: {pool.metadata}")


async def example_async_pooled_resource_manager() -> None:
    """Example demonstrating the use of an asynchronous pooled resource manager."""
    print("\n=== Async Pooled Resource Manager Example ===")

    # Create a factory function for resources
    resource_id = 0

    def create_resource() -> AsyncResource:
        nonlocal resource_id
        resource_id += 1
        return AsyncResource(resource_id)

    # Create an asynchronous pooled resource manager
    pool = AsyncPooledResourceManager(
        name="async-resource-pool",
        factory=create_resource,
        max_size=3,
        min_size=1,
        timeout=2.0,
    )

    # Add some metadata to the pool
    pool.with_metadata("created_at", time.time())
    pool.with_metadata("purpose", "async example")

    # Use resources from the pool
    async def use_resource() -> None:
        async with pool as resource:
            print(f"Using {resource} from pool {pool.name}")
            await resource.use()
            # Do something with the resource
            await asyncio.sleep(0.1)
            await resource.release()

    # Use multiple resources concurrently
    await asyncio.gather(*[use_resource() for _ in range(5)])

    print(f"Pool metadata: {pool.metadata}")


def example_timed_context() -> None:
    """Example demonstrating the use of a timed context."""
    print("\n=== Timed Context Example ===")

    # Use a timed context to measure the execution time of a block of code
    with TimedContext("sleep-operation") as timer:
        print("Sleeping for 0.5 seconds...")
        time.sleep(0.5)

    print(f"Operation '{timer.name}' took {timer.elapsed:.3f} seconds")

    # Use the timed decorator to measure the execution time of a function
    @timed("decorated-function")
    def slow_function() -> None:
        print("Executing slow function...")
        time.sleep(0.3)

    slow_function()


async def example_async_timed_context() -> None:
    """Example demonstrating the use of an asynchronous timed context."""
    print("\n=== Async Timed Context Example ===")

    # Use an asynchronous timed context to measure the execution time of a block of code
    async with AsyncTimedContext("async-sleep-operation") as timer:
        print("Sleeping asynchronously for 0.5 seconds...")
        await asyncio.sleep(0.5)

    print(f"Operation '{timer.name}' took {timer.elapsed:.3f} seconds")

    # Use the async_timed decorator to measure the execution time of an asynchronous function
    @async_timed("decorated-async-function")
    async def slow_async_function() -> None:
        print("Executing slow asynchronous function...")
        await asyncio.sleep(0.3)

    await slow_async_function()


def example_retry_context() -> None:
    """Example demonstrating the use of a retry context."""
    print("\n=== Retry Context Example ===")

    # Define a function that sometimes fails
    def unreliable_function() -> str:
        if random.random() < 0.7:  # 70% chance of failure
            raise ValueError("Random failure")
        return "Success!"

    # Use a retry context to retry the function if it fails
    try:
        with RetryContext(
            max_retries=3, delay=0.2, backoff=1.5, exceptions=ValueError
        ) as retry_ctx:
            while True:
                try:
                    result = unreliable_function()
                    print(
                        f"Function succeeded after {retry_ctx.retry_count} retries: {result}"
                    )
                    break
                except ValueError as e:
                    if retry_ctx.retry_count >= 3:
                        print(f"Function failed after {retry_ctx.retry_count} retries")
                        raise
                    print(f"Retry {retry_ctx.retry_count}: {e}")
    except ValueError:
        print("All retries failed")

    # Use the retry decorator to retry a function if it fails
    @retry(max_retries=5, delay=0.1, backoff=1.2, exceptions=ValueError)
    def decorated_unreliable_function() -> str:
        if random.random() < 0.7:  # 70% chance of failure
            raise ValueError("Random failure in decorated function")
        return "Success in decorated function!"

    try:
        result = decorated_unreliable_function()
        print(f"Decorated function succeeded: {result}")
    except ValueError:
        print("All retries failed for decorated function")


async def example_async_retry_context() -> None:
    """Example demonstrating the use of an asynchronous retry context."""
    print("\n=== Async Retry Context Example ===")

    # Define an asynchronous function that sometimes fails
    async def unreliable_async_function() -> str:
        if random.random() < 0.7:  # 70% chance of failure
            raise ValueError("Random failure in async function")
        return "Async success!"

    # Use an asynchronous retry context to retry the function if it fails
    try:
        async with AsyncRetryContext(
            max_retries=3, delay=0.2, backoff=1.5, exceptions=ValueError
        ) as retry_ctx:
            while True:
                try:
                    result = await unreliable_async_function()
                    print(
                        f"Async function succeeded after {retry_ctx.retry_count} retries: {result}"
                    )
                    break
                except ValueError as e:
                    if retry_ctx.retry_count >= 3:
                        print(
                            f"Async function failed after {retry_ctx.retry_count} retries"
                        )
                        raise
                    print(f"Async retry {retry_ctx.retry_count}: {e}")
    except ValueError:
        print("All async retries failed")

    # Use the async_retry decorator to retry an asynchronous function if it fails
    @async_retry(max_retries=5, delay=0.1, backoff=1.2, exceptions=ValueError)
    async def decorated_unreliable_async_function() -> str:
        if random.random() < 0.7:  # 70% chance of failure
            raise ValueError("Random failure in decorated async function")
        return "Success in decorated async function!"

    try:
        result = await decorated_unreliable_async_function()
        print(f"Decorated async function succeeded: {result}")
    except ValueError:
        print("All retries failed for decorated async function")


async def main() -> None:
    """Run all examples."""
    # Run synchronous examples
    example_resource_manager()
    example_pooled_resource_manager()
    example_timed_context()
    example_retry_context()

    # Run asynchronous examples
    await example_async_pooled_resource_manager()
    await example_async_timed_context()
    await example_async_retry_context()


if __name__ == "__main__":
    asyncio.run(main())
