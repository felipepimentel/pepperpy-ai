#!/usr/bin/env python
"""Example demonstrating connection pooling for network providers.

This example shows how to use the connection pooling system provided by
the PepperPy framework. It demonstrates HTTP connection pooling, custom
connection pools, and performance benefits of connection pooling.

Purpose:
    Demonstrate how to use connection pooling for network providers, including:
    - HTTP connection pooling
    - Custom connection pools
    - Performance comparison with and without pooling

Requirements:
    - Python 3.9+
    - PepperPy library
    - httpx library

Usage:
    python connection_pooling_example.py
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from pepperpy.core.connection_pool import (
    ConnectionPool,
    ConnectionPoolConfig,
    PooledResourceContext,
    get_pool,
    register_pool,
)
from pepperpy.errors import PepperpyError
from pepperpy.http.client.core import HTTPXClient, RequestOptions
from pepperpy.http.client.pool import (
    HTTPClientContext,
    HTTPPoolConfig,
    create_http_pool,
    get,
    http_client,
    initialize_default_http_pool,
)
from pepperpy.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)


async def example_http_pooling():
    """Example of HTTP connection pooling."""
    logger.info("=== HTTP Connection Pooling Example ===")

    # Initialize the default HTTP pool
    await initialize_default_http_pool()

    # Make multiple requests using the pool
    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/status/200",
        "https://httpbin.org/headers",
        "https://httpbin.org/ip",
        "https://httpbin.org/user-agent",
    ]

    # Make requests sequentially
    logger.info("Making sequential requests...")
    start_time = time.time()
    for url in urls:
        response = await get(url)
        logger.info(f"Request to {url} returned status {response.status_code}")
    sequential_time = time.time() - start_time
    logger.info(f"Sequential requests took {sequential_time:.2f} seconds")

    # Make requests concurrently
    logger.info("Making concurrent requests...")
    start_time = time.time()
    tasks = [get(url) for url in urls]
    responses = await asyncio.gather(*tasks)
    for url, response in zip(urls, responses):
        logger.info(f"Request to {url} returned status {response.status_code}")
    concurrent_time = time.time() - start_time
    logger.info(f"Concurrent requests took {concurrent_time:.2f} seconds")
    logger.info(f"Speed improvement: {sequential_time / concurrent_time:.2f}x")

    # Get pool statistics
    pool = get_pool("default_http_pool")
    logger.info(f"Pool statistics: {pool.stats}")
    logger.info(f"Pool size: {pool.size}")
    logger.info(f"Available connections: {pool.available}")
    logger.info(f"In-use connections: {pool.in_use}")


async def example_custom_http_pool():
    """Example of creating and using a custom HTTP pool."""
    logger.info("=== Custom HTTP Pool Example ===")

    # Create a custom HTTP pool with specific configuration
    config = HTTPPoolConfig(
        min_size=2,
        max_size=5,
        idle_timeout=30.0,
        max_lifetime=300.0,
        validate_on_acquire=True,
        base_url="https://httpbin.org",
        timeout=5.0,
        follow_redirects=True,
        verify_ssl=True,
        default_headers={"User-Agent": "PepperPy/1.0"},
    )
    pool = create_http_pool("custom_http_pool", config)
    await pool.initialize()

    # Make requests using the custom pool
    logger.info("Making requests with custom pool...")
    urls = ["/get", "/status/200", "/headers", "/ip", "/user-agent"]
    tasks = [get(url, pool_name="custom_http_pool") for url in urls]
    responses = await asyncio.gather(*tasks)
    for url, response in zip(urls, responses):
        logger.info(f"Request to {url} returned status {response.status_code}")

    # Get pool statistics
    logger.info(f"Pool statistics: {pool.stats}")
    logger.info(f"Pool size: {pool.size}")
    logger.info(f"Available connections: {pool.available}")
    logger.info(f"In-use connections: {pool.in_use}")


@http_client("custom_http_pool")
async def make_request_with_decorator(client, path):
    """Make a request using the http_client decorator.

    Args:
        client: HTTP client from the pool
        path: Path to request

    Returns:
        HTTP response
    """
    return await client.get(path)


async def example_http_client_decorator():
    """Example of using the http_client decorator."""
    logger.info("=== HTTP Client Decorator Example ===")

    # Make requests using the decorator
    logger.info("Making requests with decorator...")
    paths = ["/get", "/status/200", "/headers", "/ip", "/user-agent"]
    tasks = [make_request_with_decorator(path) for path in paths]
    responses = await asyncio.gather(*tasks)
    for path, response in zip(paths, responses):
        logger.info(f"Request to {path} returned status {response.status_code}")


async def example_context_manager():
    """Example of using the HTTPClientContext context manager."""
    logger.info("=== HTTP Client Context Manager Example ===")

    # Make requests using the context manager
    logger.info("Making requests with context manager...")
    async with HTTPClientContext("custom_http_pool") as client:
        response = await client.get("/get")
        logger.info(f"Request to /get returned status {response.status_code}")

        response = await client.post(
            "/post",
            options=RequestOptions(
                json={"key": "value"},
            ),
        )
        logger.info(f"Request to /post returned status {response.status_code}")

        response = await client.put(
            "/put",
            options=RequestOptions(
                json={"key": "updated_value"},
            ),
        )
        logger.info(f"Request to /put returned status {response.status_code}")


@dataclass
class DatabaseConfig(ConnectionPoolConfig):
    """Configuration for database connection pools."""

    host: str = "localhost"
    port: int = 5432
    database: str = "test"
    username: str = "user"
    password: str = "password"
    ssl: bool = False
    params: Dict[str, Any] = field(default_factory=dict)


class DatabaseConnection:
    """Mock database connection."""

    def __init__(self, config: DatabaseConfig):
        """Initialize a database connection.

        Args:
            config: Database configuration
        """
        self.config = config
        self.connected = False
        self.closed = False
        self.query_count = 0

    async def connect(self):
        """Connect to the database."""
        # Simulate connection delay
        await asyncio.sleep(0.1)
        self.connected = True
        logger.info(
            f"Connected to database {self.config.database} on {self.config.host}"
        )

    async def close(self):
        """Close the database connection."""
        # Simulate close delay
        await asyncio.sleep(0.05)
        self.connected = False
        self.closed = True
        logger.info(f"Closed connection to database {self.config.database}")

    async def execute(self, query: str):
        """Execute a query.

        Args:
            query: SQL query to execute

        Returns:
            Query result
        """
        if not self.connected:
            raise PepperpyError("Not connected to database")

        # Simulate query execution
        await asyncio.sleep(0.02)
        self.query_count += 1
        return f"Result of query: {query} (query #{self.query_count})"

    async def ping(self):
        """Ping the database to check connection."""
        if not self.connected:
            return False

        # Simulate ping
        await asyncio.sleep(0.01)
        return True


class DatabaseConnectionPool(ConnectionPool[DatabaseConnection, DatabaseConfig]):
    """Connection pool for database connections."""

    def __init__(
        self,
        name: str,
        config: Optional[DatabaseConfig] = None,
    ):
        """Initialize a database connection pool.

        Args:
            name: Name of the pool
            config: Pool configuration
        """
        super().__init__(name, config)

    def _get_default_config(self) -> DatabaseConfig:
        """Get the default configuration for the pool.

        Returns:
            Default pool configuration
        """
        return DatabaseConfig()

    async def _create_connection(self) -> DatabaseConnection:
        """Create a new database connection.

        Returns:
            New database connection

        Raises:
            PepperpyError: If connection creation fails
        """
        try:
            connection = DatabaseConnection(self.config)
            await connection.connect()
            return connection
        except Exception as e:
            raise PepperpyError(f"Failed to create database connection: {e}") from e

    async def _close_connection(self, connection: DatabaseConnection) -> None:
        """Close a database connection.

        Args:
            connection: Database connection to close

        Raises:
            PepperpyError: If connection closure fails
        """
        try:
            await connection.close()
        except Exception as e:
            raise PepperpyError(f"Failed to close database connection: {e}") from e

    async def _validate_connection(self, connection: DatabaseConnection) -> bool:
        """Validate a database connection.

        Args:
            connection: Database connection to validate

        Returns:
            True if the connection is valid, False otherwise
        """
        try:
            return await connection.ping()
        except Exception:
            return False


async def example_custom_connection_pool():
    """Example of creating and using a custom connection pool."""
    logger.info("=== Custom Connection Pool Example ===")

    # Create a custom database connection pool
    config = DatabaseConfig(
        min_size=1,
        max_size=3,
        idle_timeout=30.0,
        max_lifetime=300.0,
        validate_on_acquire=True,
        host="db.example.com",
        port=5432,
        database="example",
        username="example_user",
        password="example_password",
    )
    pool = DatabaseConnectionPool("db_pool", config)
    register_pool(pool)
    await pool.initialize()

    # Execute queries using the pool
    logger.info("Executing queries with connection pool...")
    async with PooledResourceContext("db_pool") as connection:
        result = await connection.execute("SELECT * FROM users")
        logger.info(result)

        result = await connection.execute("SELECT * FROM products")
        logger.info(result)

    # Execute multiple queries concurrently
    logger.info("Executing concurrent queries...")

    async def execute_query(query):
        async with PooledResourceContext("db_pool") as connection:
            return await connection.execute(query)

    queries = [
        "SELECT * FROM orders",
        "SELECT * FROM customers",
        "SELECT * FROM inventory",
        "SELECT * FROM suppliers",
        "SELECT * FROM categories",
    ]
    tasks = [execute_query(query) for query in queries]
    results = await asyncio.gather(*tasks)
    for query, result in zip(queries, results):
        logger.info(f"Query '{query}' result: {result}")

    # Get pool statistics
    logger.info(f"Pool statistics: {pool.stats}")
    logger.info(f"Pool size: {pool.size}")
    logger.info(f"Available connections: {pool.available}")
    logger.info(f"In-use connections: {pool.in_use}")


async def example_performance_comparison():
    """Example comparing performance with and without connection pooling."""
    logger.info("=== Performance Comparison Example ===")

    # Create a custom HTTP pool
    config = HTTPPoolConfig(
        min_size=5,
        max_size=10,
        idle_timeout=30.0,
        max_lifetime=300.0,
        validate_on_acquire=True,
        base_url="https://httpbin.org",
        timeout=5.0,
    )
    pool = create_http_pool("perf_http_pool", config)
    await pool.initialize()

    # Parameters for the test
    num_requests = 20
    paths = ["/get", "/status/200", "/headers", "/ip", "/user-agent"]
    num_iterations = len(paths) * num_requests

    # Make requests without pooling
    logger.info(f"Making {num_iterations} requests without pooling...")
    start_time = time.time()
    without_pooling_times = []

    for _ in range(num_requests):
        for path in paths:
            request_start = time.time()
            client = HTTPXClient(base_url="https://httpbin.org")
            response = await client.get(path)
            await client.client.aclose()
            request_time = time.time() - request_start
            without_pooling_times.append(request_time)

    without_pooling_total = time.time() - start_time
    without_pooling_avg = sum(without_pooling_times) / len(without_pooling_times)
    logger.info(
        f"Without pooling: {without_pooling_total:.2f} seconds total, {without_pooling_avg:.4f} seconds per request"
    )

    # Make requests with pooling
    logger.info(f"Making {num_iterations} requests with pooling...")
    start_time = time.time()
    with_pooling_times = []

    for _ in range(num_requests):
        for path in paths:
            request_start = time.time()
            response = await get(path, pool_name="perf_http_pool")
            request_time = time.time() - request_start
            with_pooling_times.append(request_time)

    with_pooling_total = time.time() - start_time
    with_pooling_avg = sum(with_pooling_times) / len(with_pooling_times)
    logger.info(
        f"With pooling: {with_pooling_total:.2f} seconds total, {with_pooling_avg:.4f} seconds per request"
    )

    # Calculate improvement
    time_improvement = without_pooling_total / with_pooling_total
    avg_improvement = without_pooling_avg / with_pooling_avg
    logger.info(f"Time improvement: {time_improvement:.2f}x faster")
    logger.info(f"Average request improvement: {avg_improvement:.2f}x faster")

    # Get pool statistics
    logger.info(f"Pool statistics: {pool.stats}")
    logger.info(f"Pool size: {pool.size}")
    logger.info(f"Available connections: {pool.available}")
    logger.info(f"In-use connections: {pool.in_use}")
    logger.info(f"Connections created: {pool.stats.created}")
    logger.info(f"Connections acquired: {pool.stats.acquired}")
    logger.info(f"Connections released: {pool.stats.released}")


async def main():
    """Run all examples."""
    try:
        await example_http_pooling()
        print()
        await example_custom_http_pool()
        print()
        await example_http_client_decorator()
        print()
        await example_context_manager()
        print()
        await example_custom_connection_pool()
        print()
        await example_performance_comparison()
    finally:
        # Close all pools
        from pepperpy.core.connection_pool import close_pools

        await close_pools()


if __name__ == "__main__":
    asyncio.run(main())
