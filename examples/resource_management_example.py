#!/usr/bin/env python
"""Example demonstrating resource management and cleanup mechanisms.

This example demonstrates the use of the resource tracking and management
system provided by the PepperPy framework, including automatic cleanup
of resources based on idle timeouts and maximum age.
"""

import asyncio
import time
from typing import List, Optional

from pepperpy.core.resource_tracker import (
    AsyncTrackedResourceManager,
    ResourceTracker,
    ResourceType,
    TrackedResourceManager,
    cleanup_all_resources,
    get_resource_stats,
    track_resource,
)
from pepperpy.utils.logging import configure_logging, get_logger

# Configure logging
configure_logging(level="INFO")
logger = get_logger(__name__)


class DatabaseConnection:
    """A simulated database connection for demonstration purposes."""

    def __init__(self, connection_id: int, db_name: str):
        """Initialize the database connection.

        Args:
            connection_id: The ID of the connection
            db_name: The name of the database
        """
        self.connection_id = connection_id
        self.db_name = db_name
        self.is_open = True
        self.queries_executed = 0
        logger.info(f"Database connection {connection_id} to {db_name} created")

    def execute_query(self, query: str) -> List[dict]:
        """Execute a query on the database.

        Args:
            query: The query to execute

        Returns:
            The query results
        """
        if not self.is_open:
            raise RuntimeError(f"Connection {self.connection_id} is closed")
        self.queries_executed += 1
        logger.info(f"Executed query on connection {self.connection_id}: {query}")
        # Simulate query execution
        time.sleep(0.1)
        return [{"result": f"Data from {self.db_name} for query: {query}"}]

    def close(self) -> None:
        """Close the database connection."""
        if not self.is_open:
            logger.warning(f"Connection {self.connection_id} is already closed")
            return
        self.is_open = False
        logger.info(
            f"Database connection {self.connection_id} to {self.db_name} closed"
        )


class AsyncDatabaseConnection:
    """A simulated asynchronous database connection for demonstration purposes."""

    def __init__(self, connection_id: int, db_name: str):
        """Initialize the asynchronous database connection.

        Args:
            connection_id: The ID of the connection
            db_name: The name of the database
        """
        self.connection_id = connection_id
        self.db_name = db_name
        self.is_open = True
        self.queries_executed = 0
        logger.info(f"Async database connection {connection_id} to {db_name} created")

    async def execute_query(self, query: str) -> List[dict]:
        """Execute a query on the database asynchronously.

        Args:
            query: The query to execute

        Returns:
            The query results
        """
        if not self.is_open:
            raise RuntimeError(f"Async connection {self.connection_id} is closed")
        self.queries_executed += 1
        logger.info(f"Executed async query on connection {self.connection_id}: {query}")
        # Simulate query execution
        await asyncio.sleep(0.1)
        return [{"result": f"Async data from {self.db_name} for query: {query}"}]

    async def close(self) -> None:
        """Close the database connection asynchronously."""
        if not self.is_open:
            logger.warning(f"Async connection {self.connection_id} is already closed")
            return
        self.is_open = False
        # Simulate closing delay
        await asyncio.sleep(0.1)
        logger.info(
            f"Async database connection {self.connection_id} to {self.db_name} closed"
        )


class DatabaseConnectionManager(TrackedResourceManager[DatabaseConnection]):
    """A resource manager for database connections."""

    def __init__(
        self,
        db_name: str,
        idle_timeout: Optional[float] = 60.0,
        max_age: Optional[float] = 300.0,
    ):
        """Initialize the database connection manager.

        Args:
            db_name: The name of the database
            idle_timeout: Timeout in seconds after which an idle connection should be closed
            max_age: Maximum age in seconds after which a connection should be closed
        """
        super().__init__(
            name=f"DatabaseConnectionManager-{db_name}",
            resource_type=ResourceType.CONNECTION,
            idle_timeout=idle_timeout,
            max_age=max_age,
        )
        self.db_name = db_name
        self.next_connection_id = 1

    def create_resource(self) -> DatabaseConnection:
        """Create a new database connection.

        Returns:
            The created database connection
        """
        connection = DatabaseConnection(self.next_connection_id, self.db_name)
        self.next_connection_id += 1
        return connection

    def cleanup_resource(self, resource: DatabaseConnection) -> None:
        """Clean up a database connection.

        Args:
            resource: The database connection to clean up
        """
        resource.close()


class AsyncDatabaseConnectionManager(
    AsyncTrackedResourceManager[AsyncDatabaseConnection]
):
    """An asynchronous resource manager for database connections."""

    def __init__(
        self,
        db_name: str,
        idle_timeout: Optional[float] = 60.0,
        max_age: Optional[float] = 300.0,
    ):
        """Initialize the asynchronous database connection manager.

        Args:
            db_name: The name of the database
            idle_timeout: Timeout in seconds after which an idle connection should be closed
            max_age: Maximum age in seconds after which a connection should be closed
        """
        super().__init__(
            name=f"AsyncDatabaseConnectionManager-{db_name}",
            resource_type=ResourceType.CONNECTION,
            idle_timeout=idle_timeout,
            max_age=max_age,
        )
        self.db_name = db_name
        self.next_connection_id = 1

    async def create_resource(self) -> AsyncDatabaseConnection:
        """Create a new asynchronous database connection.

        Returns:
            The created asynchronous database connection
        """
        connection = AsyncDatabaseConnection(self.next_connection_id, self.db_name)
        self.next_connection_id += 1
        return connection

    async def cleanup_resource(self, resource: AsyncDatabaseConnection) -> None:
        """Clean up an asynchronous database connection.

        Args:
            resource: The asynchronous database connection to clean up
        """
        await resource.close()


def example_manual_resource_tracking() -> None:
    """Example demonstrating manual resource tracking."""
    print("\n=== Manual Resource Tracking Example ===")

    # Create a database connection
    connection = DatabaseConnection(1, "example_db")

    # Track the connection with the resource tracker
    track_resource(
        resource=connection,
        resource_type=ResourceType.CONNECTION,
        cleanup_func=lambda conn: conn.close(),
        idle_timeout=5.0,  # 5 seconds
        max_age=30.0,  # 30 seconds
        metadata={"purpose": "example", "user": "demo"},
    )

    # Use the connection
    connection.execute_query("SELECT * FROM example_table")

    # Get resource statistics
    print("\nResource statistics after creating connection:")
    stats = get_resource_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Wait for the idle timeout to trigger cleanup
    print("\nWaiting for idle timeout (5 seconds)...")
    time.sleep(6)

    # Get resource statistics again
    print("\nResource statistics after idle timeout:")
    stats = get_resource_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


def example_resource_manager() -> None:
    """Example demonstrating the use of a resource manager."""
    print("\n=== Resource Manager Example ===")

    # Create a database connection manager
    manager = DatabaseConnectionManager(
        db_name="example_db",
        idle_timeout=5.0,  # 5 seconds
        max_age=30.0,  # 30 seconds
    )

    # Use a connection with a context manager
    with manager as connection:
        print(f"Using connection: {connection.connection_id}")
        connection.execute_query("SELECT * FROM example_table")

    # Get resource statistics
    print("\nResource statistics after using connection:")
    stats = get_resource_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Wait for the idle timeout to trigger cleanup
    print("\nWaiting for idle timeout (5 seconds)...")
    time.sleep(6)

    # Get resource statistics again
    print("\nResource statistics after idle timeout:")
    stats = get_resource_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


async def example_async_resource_manager() -> None:
    """Example demonstrating the use of an asynchronous resource manager."""
    print("\n=== Async Resource Manager Example ===")

    # Create an asynchronous database connection manager
    manager = AsyncDatabaseConnectionManager(
        db_name="example_async_db",
        idle_timeout=5.0,  # 5 seconds
        max_age=30.0,  # 30 seconds
    )

    # Use a connection with an asynchronous context manager
    async with manager as connection:
        print(f"Using async connection: {connection.connection_id}")
        await connection.execute_query("SELECT * FROM example_async_table")

    # Get resource statistics
    print("\nResource statistics after using async connection:")
    stats = get_resource_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Wait for the idle timeout to trigger cleanup
    print("\nWaiting for idle timeout (5 seconds)...")
    await asyncio.sleep(6)

    # Get resource statistics again
    print("\nResource statistics after idle timeout:")
    stats = get_resource_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


def example_resource_cleanup() -> None:
    """Example demonstrating resource cleanup."""
    print("\n=== Resource Cleanup Example ===")

    # Create multiple database connections
    connections = []
    for i in range(5):
        connection = DatabaseConnection(i + 1, f"example_db_{i}")
        track_resource(
            resource=connection,
            resource_type=ResourceType.CONNECTION,
            cleanup_func=lambda conn: conn.close(),
            idle_timeout=60.0,  # 60 seconds
            max_age=300.0,  # 300 seconds
        )
        connections.append(connection)

    # Use the connections
    for i, connection in enumerate(connections):
        connection.execute_query(f"SELECT * FROM table_{i}")

    # Get resource statistics
    print("\nResource statistics after creating connections:")
    stats = get_resource_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Clean up all resources
    print("\nCleaning up all resources...")
    cleaned_up, errors = cleanup_all_resources()
    print(f"Cleaned up {cleaned_up} resources with {errors} errors")

    # Get resource statistics again
    print("\nResource statistics after cleanup:")
    stats = get_resource_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


async def main() -> None:
    """Run the example."""
    # Set up the resource tracker
    tracker = ResourceTracker()
    tracker.set_cleanup_interval(10.0)  # 10 seconds

    # Run the examples
    example_manual_resource_tracking()
    example_resource_manager()
    await example_async_resource_manager()
    example_resource_cleanup()


if __name__ == "__main__":
    asyncio.run(main())
