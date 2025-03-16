"""Connection pooling for network providers.

This module provides connection pooling functionality for network providers,
including HTTP clients, database connections, and other network resources.

Typical usage:
    from pepperpy.infra.connection import ConnectionPool, pooled_resource

    # Create a custom connection pool
    class MyConnectionPool(ConnectionPool):
        async def _create_connection(self):
            # Create a connection
            return my_connection_library.connect()

        async def _close_connection(self, connection):
            # Close a connection
            await connection.close()

        async def _validate_connection(self, connection):
            # Validate a connection
            return await connection.is_valid()

    # Register the pool
    pool = MyConnectionPool("my_pool")
    register_pool(pool)
    await initialize_pools()

    # Use the pool with a context manager
    async with pooled_resource("my_pool") as connection:
        # Use the connection
        result = await connection.execute("SELECT * FROM table")

    # Or use the pool with a decorator
    @pooled_resource("my_pool")
    async def my_function(connection):
        # Use the connection
        result = await connection.execute("SELECT * FROM table")
        return result

    # Close all pools when done
    await close_pools()
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, cast

from pepperpy.infra.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for connection objects
T = TypeVar("T")
# Type variable for connection pool configuration
C = TypeVar("C")


class PoolStatus(Enum):
    """Status of a connection pool.

    Args:
        INITIALIZING: The pool is initializing
        READY: The pool is ready for use
        CLOSING: The pool is closing
        CLOSED: The pool is closed
    """

    INITIALIZING = auto()
    READY = auto()
    CLOSING = auto()
    CLOSED = auto()


@dataclass
class ConnectionStats:
    """Statistics for a connection pool.

    Args:
        created: Number of connections created
        acquired: Number of connections acquired
        released: Number of connections released
        errors: Number of connection errors
        timeouts: Number of connection timeouts
        idle_closed: Number of idle connections closed
        max_size_reached: Number of times the maximum pool size was reached
        current_size: Current number of connections in the pool
        in_use: Number of connections currently in use
        wait_time: Average wait time for acquiring a connection
        total_wait_time: Total wait time for acquiring connections
        last_error_time: Timestamp of the last error
        last_error: The last error that occurred
    """

    created: int = 0
    acquired: int = 0
    released: int = 0
    errors: int = 0
    timeouts: int = 0
    idle_closed: int = 0
    max_size_reached: int = 0
    current_size: int = 0
    in_use: int = 0
    wait_time: float = 0.0
    total_wait_time: float = 0.0
    last_error_time: Optional[float] = None
    last_error: Optional[Exception] = None


@dataclass
class ConnectionPoolConfig:
    """Configuration for a connection pool.

    Args:
        min_size: Minimum number of connections to maintain
        max_size: Maximum number of connections to allow
        acquire_timeout: Timeout for acquiring a connection
        idle_timeout: Timeout for idle connections
        max_lifetime: Maximum lifetime of a connection
        validate_on_acquire: Whether to validate connections when acquired
        validate_interval: Interval for validating connections
        retry_attempts: Number of retry attempts for failed operations
        retry_delay: Delay between retry attempts
        health_check_interval: Interval for health checks
        params: Additional parameters for the connection pool
    """

    # Pool size limits
    min_size: int = 1
    max_size: int = 10

    # Timeouts
    acquire_timeout: float = 10.0
    idle_timeout: float = 60.0
    max_lifetime: float = 3600.0

    # Connection validation
    validate_on_acquire: bool = True
    validate_interval: float = 30.0

    # Retry settings
    retry_attempts: int = 3
    retry_delay: float = 1.0

    # Health check
    health_check_interval: float = 30.0

    # Additional configuration
    params: Dict[str, Any] = field(default_factory=dict)


class ConnectionPool(Generic[T, C], ABC):
    """Base class for connection pools.

    This class provides the core functionality for connection pooling,
    including connection creation, validation, and lifecycle management.

    Args:
        name: The name of the pool
        config: The configuration for the pool
    """

    def __init__(
        self,
        name: str,
        config: Optional[C] = None,
    ):
        """Initialize a connection pool.

        Args:
            name: The name of the pool
            config: The configuration for the pool
        """
        self.name = name
        self.config = config or self._get_default_config()
        self._status = PoolStatus.INITIALIZING
        self._connections: List[T] = []
        self._available: asyncio.Queue[T] = asyncio.Queue()
        self._connection_info: Dict[T, Dict[str, Any]] = {}
        self._maintenance_task: Optional[asyncio.Task] = None
        self._stats = ConnectionStats()
        self._lock = asyncio.Lock()

    @abstractmethod
    def _get_default_config(self) -> C:
        """Get the default configuration for the pool.

        Returns:
            The default configuration
        """
        pass

    @abstractmethod
    async def _create_connection(self) -> T:
        """Create a new connection.

        Returns:
            A new connection
        """
        pass

    @abstractmethod
    async def _close_connection(self, connection: T) -> None:
        """Close a connection.

        Args:
            connection: The connection to close
        """
        pass

    @abstractmethod
    async def _validate_connection(self, connection: T) -> bool:
        """Validate a connection.

        Args:
            connection: The connection to validate

        Returns:
            True if the connection is valid, False otherwise
        """
        pass

    async def initialize(self) -> None:
        """Initialize the connection pool.

        This method creates the initial connections and starts the maintenance task.
        """
        if self._status != PoolStatus.INITIALIZING:
            return

        try:
            # Create initial connections
            min_size = self._get_min_size()
            for _ in range(min_size):
                connection = await self._create_connection()
                self._connections.append(connection)
                self._connection_info[connection] = {
                    "created_at": time.time(),
                    "last_used": time.time(),
                    "last_validated": time.time(),
                    "in_use": False,
                }
                await self._available.put(connection)
                self._stats.created += 1
                self._stats.current_size += 1

            # Start maintenance task
            self._maintenance_task = asyncio.create_task(self._run_maintenance())

            # Update status
            self._status = PoolStatus.READY
            logger.info(
                f"Connection pool '{self.name}' initialized with {min_size} connections"
            )
        except Exception as e:
            self._status = PoolStatus.CLOSED
            self._stats.errors += 1
            self._stats.last_error = e
            self._stats.last_error_time = time.time()
            logger.error(f"Failed to initialize connection pool '{self.name}': {e}")
            raise

    async def _run_maintenance(self) -> None:
        """Run the maintenance task for the connection pool.

        This task runs periodically to validate connections, close idle connections,
        and ensure the minimum pool size is maintained.
        """
        while True:
            try:
                # Sleep for the health check interval
                await asyncio.sleep(self._get_health_check_interval())

                # Skip if the pool is not ready
                if self._status != PoolStatus.READY:
                    continue

                # Get the current time
                now = time.time()

                # Check each connection
                async with self._lock:
                    for connection in list(self._connections):
                        # Skip connections that are in use
                        if self._connection_info[connection]["in_use"]:
                            continue

                        # Check if the connection is idle
                        last_used = self._connection_info[connection]["last_used"]
                        idle_time = now - last_used
                        if idle_time > self._get_idle_timeout():
                            # Close the idle connection
                            logger.debug(
                                f"Connection in pool '{self.name}' has been idle for "
                                f"{idle_time:.2f} seconds, closing"
                            )
                            await self._close_connection(connection)
                            self._connections.remove(connection)
                            del self._connection_info[connection]
                            self._stats.current_size -= 1
                            self._stats.idle_closed += 1
                            continue

                        # Check if the connection needs validation
                        last_validated = self._connection_info[connection][
                            "last_validated"
                        ]
                        validation_age = now - last_validated
                        if validation_age > self._get_validate_interval():
                            # Validate the connection
                            is_valid = await self._validate_connection(connection)
                            self._connection_info[connection]["last_validated"] = now

                            if not is_valid:
                                # Close the invalid connection
                                logger.warning(
                                    f"Connection in pool '{self.name}' failed validation, closing"
                                )
                                await self._close_connection(connection)
                                self._connections.remove(connection)
                                del self._connection_info[connection]
                                self._stats.current_size -= 1
                                continue

                    # Ensure minimum pool size
                    current_size = len(self._connections)
                    min_size = self._get_min_size()
                    if current_size < min_size:
                        # Create new connections to reach the minimum size
                        for _ in range(min_size - current_size):
                            connection = await self._create_connection()
                            self._connections.append(connection)
                            self._connection_info[connection] = {
                                "created_at": now,
                                "last_used": now,
                                "last_validated": now,
                                "in_use": False,
                            }
                            await self._available.put(connection)
                            self._stats.created += 1
                            self._stats.current_size += 1
            except asyncio.CancelledError:
                # Task was cancelled, exit
                break
            except Exception as e:
                # Log the error and continue
                logger.error(f"Error in maintenance task for pool '{self.name}': {e}")
                self._stats.errors += 1
                self._stats.last_error = e
                self._stats.last_error_time = time.time()

    async def close(self) -> None:
        """Close the connection pool.

        This method closes all connections and stops the maintenance task.
        """
        if self._status == PoolStatus.CLOSED:
            return

        self._status = PoolStatus.CLOSING
        logger.info(f"Closing connection pool '{self.name}'")

        # Cancel maintenance task
        if self._maintenance_task is not None:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass
            self._maintenance_task = None

        # Close all connections
        for connection in self._connections:
            try:
                await self._close_connection(connection)
            except Exception as e:
                logger.error(f"Error closing connection in pool '{self.name}': {e}")
                self._stats.errors += 1
                self._stats.last_error = e
                self._stats.last_error_time = time.time()

        # Clear data structures
        self._connections = []
        self._connection_info = {}
        self._available = asyncio.Queue()
        self._stats.current_size = 0
        self._stats.in_use = 0

        # Update status
        self._status = PoolStatus.CLOSED
        logger.info(f"Connection pool '{self.name}' closed")

    async def acquire(self) -> T:
        """Acquire a connection from the pool.

        Returns:
            A connection from the pool

        Raises:
            TimeoutError: If a connection could not be acquired within the timeout
            RuntimeError: If the pool is not ready
        """
        if self._status != PoolStatus.READY:
            raise RuntimeError(f"Connection pool '{self.name}' is not ready")

        # Record start time for stats
        start_time = time.time()

        # Try to get a connection from the pool
        try:
            # Get the acquire timeout
            acquire_timeout = self._get_acquire_timeout()

            # Try to get a connection from the available queue
            try:
                connection = await asyncio.wait_for(
                    self._available.get(), timeout=acquire_timeout
                )
            except asyncio.TimeoutError:
                # If we timed out, check if we can create a new connection
                async with self._lock:
                    if len(self._connections) < self._get_max_size():
                        # Create a new connection
                        connection = await self._create_connection()
                        self._connections.append(connection)
                        self._connection_info[connection] = {
                            "created_at": time.time(),
                            "last_used": time.time(),
                            "last_validated": time.time(),
                            "in_use": False,
                        }
                        self._stats.created += 1
                        self._stats.current_size += 1
                    else:
                        # We've reached the maximum pool size
                        self._stats.max_size_reached += 1
                        self._stats.timeouts += 1
                        logger.warning(
                            f"Connection pool '{self.name}' reached maximum size, "
                            f"could not acquire connection within {acquire_timeout} seconds"
                        )
                        raise TimeoutError(
                            f"Could not acquire connection from pool '{self.name}' "
                            f"within {acquire_timeout} seconds"
                        )

            # Validate the connection if needed
            if self._should_validate(connection):
                # Validate the connection
                is_valid = await self._validate_connection(connection)
                self._connection_info[connection]["last_validated"] = time.time()

                if not is_valid:
                    # Close the invalid connection
                    logger.warning(
                        f"Connection in pool '{self.name}' failed validation, creating new connection"
                    )
                    await self._close_connection(connection)
                    self._connections.remove(connection)
                    del self._connection_info[connection]
                    self._stats.current_size -= 1

                    # Create a new connection
                    connection = await self._create_connection()
                    self._connections.append(connection)
                    self._connection_info[connection] = {
                        "created_at": time.time(),
                        "last_used": time.time(),
                        "last_validated": time.time(),
                        "in_use": False,
                    }
                    self._stats.created += 1
                    self._stats.current_size += 1

            # Mark the connection as in use
            self._connection_info[connection]["in_use"] = True
            self._connection_info[connection]["last_used"] = time.time()
            self._stats.acquired += 1
            self._stats.in_use += 1

            # Update wait time stats
            wait_time = time.time() - start_time
            self._stats.total_wait_time += wait_time
            self._stats.wait_time = self._stats.total_wait_time / self._stats.acquired

            return connection
        except Exception as e:
            if not isinstance(e, TimeoutError):
                # Record the error
                self._stats.errors += 1
                self._stats.last_error = e
                self._stats.last_error_time = time.time()
                logger.error(f"Error acquiring connection from pool '{self.name}': {e}")
            raise

    async def release(self, connection: T) -> None:
        """Release a connection back to the pool.

        Args:
            connection: The connection to release

        Raises:
            ValueError: If the connection is not from this pool
            RuntimeError: If the pool is not ready
        """
        if self._status != PoolStatus.READY:
            # If the pool is closing or closed, just close the connection
            if connection in self._connection_info:
                try:
                    await self._close_connection(connection)
                except Exception as e:
                    logger.error(f"Error closing connection in pool '{self.name}': {e}")
                    self._stats.errors += 1
                    self._stats.last_error = e
                    self._stats.last_error_time = time.time()
            return

        # Check if the connection is from this pool
        if connection not in self._connection_info:
            raise ValueError(f"Connection is not from pool '{self.name}'")

        # Check if the connection is marked as in use
        if not self._connection_info[connection]["in_use"]:
            logger.warning(
                f"Connection in pool '{self.name}' was released but was not marked as in use"
            )
            return

        # Mark the connection as not in use
        self._connection_info[connection]["in_use"] = False
        self._connection_info[connection]["last_used"] = time.time()
        self._stats.released += 1
        self._stats.in_use -= 1

        # Check if the connection is expired
        if self._is_expired(connection):
            # Close the expired connection
            logger.debug(f"Connection in pool '{self.name}' has expired, closing")
            await self._close_connection(connection)
            self._connections.remove(connection)
            del self._connection_info[connection]
            self._stats.current_size -= 1

            # Create a new connection if needed
            if len(self._connections) < self._get_min_size():
                connection = await self._create_connection()
                self._connections.append(connection)
                self._connection_info[connection] = {
                    "created_at": time.time(),
                    "last_used": time.time(),
                    "last_validated": time.time(),
                    "in_use": False,
                }
                self._stats.created += 1
                self._stats.current_size += 1
                await self._available.put(connection)
        else:
            # Put the connection back in the available queue
            await self._available.put(connection)

    def _should_validate(self, connection: T) -> bool:
        """Check if a connection should be validated.

        Args:
            connection: The connection to check

        Returns:
            True if the connection should be validated, False otherwise
        """
        # Skip validation if not enabled
        if not self._get_validate_on_acquire():
            return False

        # Get the last validation time
        last_validated = self._connection_info[connection]["last_validated"]
        validation_age = time.time() - last_validated

        # Validate if the validation interval has passed
        return bool(validation_age > self._get_validate_interval())

    def _is_expired(self, connection: T) -> bool:
        """Check if a connection is expired.

        Args:
            connection: The connection to check

        Returns:
            True if the connection is expired, False otherwise
        """
        # Get the creation time
        created_at = self._connection_info[connection]["created_at"]
        age = time.time() - created_at

        # Check if the connection has exceeded its maximum lifetime
        return bool(age > self._get_max_lifetime())

    def _get_min_size(self) -> int:
        """Get the minimum pool size.

        Returns:
            The minimum pool size
        """
        return getattr(self.config, "min_size", 1)

    def _get_max_size(self) -> int:
        """Get the maximum pool size.

        Returns:
            The maximum pool size
        """
        return getattr(self.config, "max_size", 10)

    def _get_acquire_timeout(self) -> float:
        """Get the acquire timeout.

        Returns:
            The acquire timeout in seconds
        """
        return getattr(self.config, "acquire_timeout", 10.0)

    def _get_idle_timeout(self) -> float:
        """Get the idle timeout.

        Returns:
            The idle timeout in seconds
        """
        return getattr(self.config, "idle_timeout", 60.0)

    def _get_max_lifetime(self) -> float:
        """Get the maximum connection lifetime.

        Returns:
            The maximum connection lifetime in seconds
        """
        return getattr(self.config, "max_lifetime", 3600.0)

    def _get_validate_on_acquire(self) -> bool:
        """Get whether to validate connections when acquired.

        Returns:
            True if connections should be validated when acquired, False otherwise
        """
        return getattr(self.config, "validate_on_acquire", True)

    def _get_validate_interval(self) -> float:
        """Get the validation interval.

        Returns:
            The validation interval in seconds
        """
        return getattr(self.config, "validate_interval", 30.0)

    def _get_health_check_interval(self) -> float:
        """Get the health check interval.

        Returns:
            The health check interval in seconds
        """
        return getattr(self.config, "health_check_interval", 30.0)

    def _get_retry_attempts(self) -> int:
        """Get the number of retry attempts.

        Returns:
            The number of retry attempts
        """
        return getattr(self.config, "retry_attempts", 3)

    def _get_retry_delay(self) -> float:
        """Get the retry delay.

        Returns:
            The retry delay in seconds
        """
        return getattr(self.config, "retry_delay", 1.0)

    @property
    def status(self) -> PoolStatus:
        """Get the status of the pool.

        Returns:
            The status of the pool
        """
        return self._status

    @property
    def size(self) -> int:
        """Get the current size of the pool.

        Returns:
            The current size of the pool
        """
        return self._stats.current_size

    @property
    def available(self) -> int:
        """Get the number of available connections.

        Returns:
            The number of available connections
        """
        return self._available.qsize()

    @property
    def in_use(self) -> int:
        """Get the number of connections in use.

        Returns:
            The number of connections in use
        """
        return self._stats.in_use


# Global registry of connection pools
_pools: Dict[str, ConnectionPool] = {}


def register_pool(pool: ConnectionPool) -> None:
    """Register a connection pool.

    Args:
        pool: The connection pool to register

    Raises:
        ValueError: If a pool with the same name is already registered
    """
    if pool.name in _pools:
        raise ValueError(f"Connection pool '{pool.name}' is already registered")
    _pools[pool.name] = pool
    logger.info(f"Registered connection pool '{pool.name}'")


def get_pool(name: str) -> ConnectionPool:
    """Get a connection pool by name.

    Args:
        name: The name of the pool to get

    Returns:
        The connection pool

    Raises:
        ValueError: If no pool with the given name is registered
    """
    if name not in _pools:
        raise ValueError(f"No connection pool registered with name '{name}'")
    return _pools[name]


def unregister_pool(name: str) -> None:
    """Unregister a connection pool.

    Args:
        name: The name of the pool to unregister

    Raises:
        ValueError: If no pool with the given name is registered
    """
    if name not in _pools:
        raise ValueError(f"No connection pool registered with name '{name}'")
    del _pools[name]
    logger.info(f"Unregistered connection pool '{name}'")


async def initialize_pools() -> None:
    """Initialize all registered connection pools."""
    for name, pool in _pools.items():
        await pool.initialize()


async def close_pools() -> None:
    """Close all registered connection pools."""
    for name, pool in _pools.items():
        await pool.close()


async def get_connection(pool_name: str) -> Any:
    """Get a connection from a pool.

    Args:
        pool_name: The name of the pool to get a connection from

    Returns:
        A connection from the pool

    Raises:
        ValueError: If no pool with the given name is registered
    """
    pool = get_pool(pool_name)
    return await pool.acquire()


async def release_connection(pool_name: str, connection: Any) -> None:
    """Release a connection back to a pool.

    Args:
        pool_name: The name of the pool to release the connection to
        connection: The connection to release

    Raises:
        ValueError: If no pool with the given name is registered
    """
    pool = get_pool(pool_name)
    await pool.release(connection)


class PooledResourceContext(Generic[T]):
    """Context manager for pooled resources.

    This context manager acquires a connection from a pool when entered,
    and releases it when exited.

    Args:
        pool_name: The name of the pool to get a connection from
    """

    def __init__(self, pool_name: str):
        """Initialize a pooled resource context.

        Args:
            pool_name: The name of the pool to get a connection from
        """
        self.pool_name = pool_name
        self.connection: Optional[T] = None

    async def __aenter__(self) -> T:
        """Enter the context manager.

        Returns:
            A connection from the pool

        Raises:
            ValueError: If no pool with the given name is registered
        """
        connection = await get_connection(self.pool_name)
        self.connection = connection
        return cast(T, connection)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager.

        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The exception traceback, if an exception was raised
        """
        if self.connection is not None:
            await release_connection(self.pool_name, self.connection)
            self.connection = None


def pooled_resource(pool_name: str) -> Callable:
    """Decorator for functions that use pooled resources.

    This decorator acquires a connection from a pool before calling the function,
    and releases it after the function returns.

    Args:
        pool_name: The name of the pool to get a connection from

    Returns:
        A decorator for functions that use pooled resources
    """

    def decorator(func: Callable) -> Callable:
        """Decorator for functions that use pooled resources.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """

        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper for functions that use pooled resources.

            Args:
                *args: Positional arguments for the function
                **kwargs: Keyword arguments for the function

            Returns:
                The result of the function

            Raises:
                ValueError: If no pool with the given name is registered
            """
            # Use a typed context manager to get a properly typed connection
            pool_context: PooledResourceContext[Any] = PooledResourceContext(pool_name)
            async with pool_context as connection:
                return await func(connection, *args, **kwargs)

        return wrapper

    return decorator
