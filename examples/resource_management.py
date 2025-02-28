"""Example demonstrating resource management in PepperPy.

This example shows how to:
1. Create and use resources with automatic lifecycle management
2. Handle resource initialization and cleanup
3. Use resource sessions for automatic cleanup
4. Configure automatic periodic cleanup
5. Handle resource errors properly
"""

import asyncio
from datetime import UTC, datetime, timedelta

from pepperpy.core.common.resources import resource_session
from pepperpy.memory.errors import MemoryError, MemoryKeyError
from pepperpy.memory.simple import SimpleMemory


async def basic_memory_example():
    """Demonstrate basic memory resource usage."""
    # Create memory resource with automatic cleanup
    memory = SimpleMemory(
        auto_cleanup=True,
        cleanup_interval=3600,  # Clean up expired entries every hour
    )

    try:
        # Initialize memory
        await memory.initialize()

        # Store some values
        await memory.store("user_id", "12345")
        await memory.store(
            "session_token",
            "abc123",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        # Retrieve values
        user_id = await memory.retrieve("user_id")
        print(f"User ID: {user_id}")

        token = await memory.retrieve("session_token")
        print(f"Session Token: {token}")

    except MemoryError as e:
        print(f"Memory operation failed: {e}")
        print(f"Error code: {e.code}")
        print(f"Error details: {e.details}")

    finally:
        # Clean up when done
        await memory.cleanup()


async def session_example():
    """Demonstrate using resource sessions."""
    # Resource session handles initialization and cleanup
    async with resource_session(SimpleMemory()) as memory:
        try:
            # Store temporary data
            await memory.store(
                "temp_data",
                {"status": "processing"},
                expires_at=datetime.now(UTC) + timedelta(minutes=5),
            )

            # Process data
            data = await memory.retrieve("temp_data")
            print(f"Processing data: {data}")

        except MemoryKeyError as e:
            print(f"Key error: {e}")
        except MemoryError as e:
            print(f"Memory error: {e}")

    # Memory is automatically cleaned up when session ends


async def expiration_example():
    """Demonstrate automatic cleanup of expired entries."""
    memory = SimpleMemory(cleanup_interval=2)  # Clean up every 2 seconds

    try:
        await memory.initialize()

        # Store value that expires in 1 second
        await memory.store(
            "short_lived",
            "temporary value",
            expires_at=datetime.now(UTC) + timedelta(seconds=1),
        )

        # Wait for expiration
        print("Waiting for value to expire...")
        await asyncio.sleep(3)

        try:
            # Try to retrieve expired value
            value = await memory.retrieve("short_lived")
            print("Value still exists:", value)
        except MemoryKeyError:
            print("Value has expired and was cleaned up")

    finally:
        await memory.cleanup()


async def main():
    """Run examples."""
    print("\n=== Basic Memory Example ===")
    await basic_memory_example()

    print("\n=== Resource Session Example ===")
    await session_example()

    print("\n=== Expiration Example ===")
    await expiration_example()


if __name__ == "__main__":
    asyncio.run(main())
