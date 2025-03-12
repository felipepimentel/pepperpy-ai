"""Connection pooling for network providers.

This module provides connection pooling functionality for network providers,
including HTTP clients, database connections, and other network resources.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from pepperpy.errors import PepperpyError

# Type variable for connection objects
T = TypeVar("T")
# Type variable for connection pool configuration
C = TypeVar("C")


class PoolStatus(Enum):
    """Status of a connection pool."""

    INITIALIZING = auto()
    READY = auto()
    CLOSING = auto()
    CLOSED = auto()


@dataclass
class ConnectionStats:
    """Statistics for a connection pool."""

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
    """Configuration for a connection pool."""

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
    """Abstract base class for connection pools.

    This class provides the interface for connection pools and implements
    common functionality for connection management.
    """

    def __init__(
        self,
        name: str,
        config: Optional[C] = None,
    ):
        """Initialize a connection pool.

        Args:
            name: Name of the pool
            config: Pool configuration
        """
        self.name = name
        self.config = config or self._get_default_config()

        # Pool state
        self._status = PoolStatus.INITIALIZING
        self._available: List[T] = []
        self._in_use: Dict[T, float] = {}
        self._last_validation: Dict[T, float] = {}
        self._creation_time: Dict[T, float] = {}

        # Synchronization
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)

        # Statistics
        self.stats = ConnectionStats()

    @abstractmethod
    def _get_default_config(self) -> C:
        """Get the default configuration for the pool.

        Returns:
            Default pool configuration
        """
        pass

    @abstractmethod
    async def _create_connection(self) -> T:
        """Create a new connection.

        Returns:
            New connection

        Raises:
            PepperpyError: If connection creation fails
        """
        pass

    @abstractmethod
    async def _close_connection(self, connection: T) -> None:
        """Close a connection.

        Args:
            connection: Connection to close

        Raises:
            PepperpyError: If connection closure fails
        """
        pass

    @abstractmethod
    async def _validate_connection(self, connection: T) -> bool:
        """Validate a connection.

        Args:
            connection: Connection to validate

        Returns:
            True if the connection is valid, False otherwise
        """
        pass

    async def initialize(self) -> None:
        """Initialize the connection pool.

        This method creates the minimum number of connections and
        starts the background tasks for pool maintenance.

        Raises:
            PepperpyError: If pool initialization fails
        """
        async with self._lock:
            if self._status != PoolStatus.INITIALIZING:
                return

            # Create minimum number of connections
            for _ in range(self._get_min_size()):
                try:
                    connection = await self._create_connection()
                    self._available.append(connection)
                    self._creation_time[connection] = time.time()
                    self._last_validation[connection] = time.time()
                    self.stats.created += 1
                    self.stats.current_size += 1
                except Exception as e:
                    self.stats.errors += 1
                    self.stats.last_error = e
                    self.stats.last_error_time = time.time()
                    raise PepperpyError(
                        f"Failed to initialize connection pool '{self.name}': {e}"
                    ) from e

            # Start background tasks
            asyncio.create_task(self._maintenance_task())

            # Update status
            self._status = PoolStatus.READY

    async def close(self) -> None:
        """Close the connection pool.

        This method closes all connections and stops the background tasks.

        Raises:
            PepperpyError: If pool closure fails
        """
        async with self._lock:
            if self._status in (PoolStatus.CLOSING, PoolStatus.CLOSED):
                return

            self._status = PoolStatus.CLOSING

            # Close all available connections
            for connection in self._available:
                try:
                    await self._close_connection(connection)
                except Exception as e:
                    self.stats.errors += 1
                    self.stats.last_error = e
                    self.stats.last_error_time = time.time()

            # Close all in-use connections
            for connection in list(self._in_use.keys()):
                try:
                    await self._close_connection(connection)
                except Exception as e:
                    self.stats.errors += 1
                    self.stats.last_error = e
                    self.stats.last_error_time = time.time()

            # Clear pool state
            self._available.clear()
            self._in_use.clear()
            self._last_validation.clear()
            self._creation_time.clear()
            self.stats.current_size = 0
            self.stats.in_use = 0

            # Update status
            self._status = PoolStatus.CLOSED

    async def acquire(self) -> T:
        """Acquire a connection from the pool.

        Returns:
            Connection from the pool

        Raises:
            PepperpyError: If a connection cannot be acquired
        """
        if self._status != PoolStatus.READY:
            raise PepperpyError(
                f"Cannot acquire connection from pool '{self.name}': "
                f"pool is {self._status.name.lower()}"
            )

        start_time = time.time()

        async with self._lock:
            # Try to get a connection from the available pool
            while True:
                # Check if we have an available connection
                if self._available:
                    connection = self._available.pop(0)

                    # Validate the connection if needed
                    if self._should_validate(connection):
                        is_valid = await self._validate_connection(connection)
                        self._last_validation[connection] = time.time()

                        if not is_valid:
                            # Close the invalid connection
                            try:
                                await self._close_connection(connection)
                            except Exception as e:
                                self.stats.errors += 1
                                self.stats.last_error = e
                                self.stats.last_error_time = time.time()

                            # Remove from pool state
                            if connection in self._creation_time:
                                del self._creation_time[connection]
                            if connection in self._last_validation:
                                del self._last_validation[connection]

                            self.stats.current_size -= 1

                            # Try again
                            continue

                    # Mark the connection as in use
                    self._in_use[connection] = time.time()
                    self.stats.acquired += 1
                    self.stats.in_use += 1

                    # Calculate wait time
                    wait_time = time.time() - start_time
                    self.stats.wait_time = wait_time
                    self.stats.total_wait_time += wait_time

                    return connection

                # If we don't have an available connection, try to create one
                if self.stats.current_size < self._get_max_size():
                    try:
                        connection = await self._create_connection()
                        self._creation_time[connection] = time.time()
                        self._last_validation[connection] = time.time()
                        self._in_use[connection] = time.time()
                        self.stats.created += 1
                        self.stats.acquired += 1
                        self.stats.current_size += 1
                        self.stats.in_use += 1

                        # Calculate wait time
                        wait_time = time.time() - start_time
                        self.stats.wait_time = wait_time
                        self.stats.total_wait_time += wait_time

                        return connection
                    except Exception as e:
                        self.stats.errors += 1
                        self.stats.last_error = e
                        self.stats.last_error_time = time.time()
                        raise PepperpyError(
                            f"Failed to create connection in pool '{self.name}': {e}"
                        ) from e
                else:
                    self.stats.max_size_reached += 1

                # If we've reached the max size, wait for a connection to be released
                if time.time() - start_time > self._get_acquire_timeout():
                    self.stats.timeouts += 1
                    raise PepperpyError(
                        f"Timed out waiting for connection from pool '{self.name}'"
                    )

                # Wait for a connection to be released
                try:
                    await asyncio.wait_for(
                        self._condition.wait(),
                        timeout=self._get_acquire_timeout()
                        - (time.time() - start_time),
                    )
                except asyncio.TimeoutError:
                    self.stats.timeouts += 1
                    raise PepperpyError(
                        f"Timed out waiting for connection from pool '{self.name}'"
                    )

    async def release(self, connection: T) -> None:
        """Release a connection back to the pool.

        Args:
            connection: Connection to release

        Raises:
            PepperpyError: If the connection is not in use
        """
        if self._status != PoolStatus.READY:
            # If the pool is closing or closed, just close the connection
            if self._status in (PoolStatus.CLOSING, PoolStatus.CLOSED):
                try:
                    await self._close_connection(connection)
                except Exception:
                    pass
                return

            raise PepperpyError(
                f"Cannot release connection to pool '{self.name}': "
                f"pool is {self._status.name.lower()}"
            )

        async with self._lock:
            # Check if the connection is in use
            if connection not in self._in_use:
                raise PepperpyError(
                    f"Connection is not in use and cannot be released to pool '{self.name}'"
                )

            # Remove from in-use list
            del self._in_use[connection]
            self.stats.released += 1
            self.stats.in_use -= 1

            # Check if the connection is too old
            if self._is_expired(connection):
                try:
                    await self._close_connection(connection)
                except Exception as e:
                    self.stats.errors += 1
                    self.stats.last_error = e
                    self.stats.last_error_time = time.time()

                # Remove from pool state
                if connection in self._creation_time:
                    del self._creation_time[connection]
                if connection in self._last_validation:
                    del self._last_validation[connection]

                self.stats.current_size -= 1
            else:
                # Add back to available pool
                self._available.append(connection)

            # Notify waiters
            self._condition.notify_all()

    async def _maintenance_task(self) -> None:
        """Background task for pool maintenance.

        This task periodically checks for idle connections and closes them,
        and validates connections that haven't been validated recently.
        """
        while self._status == PoolStatus.READY:
            try:
                await asyncio.sleep(
                    min(
                        self._get_idle_timeout() / 2,
                        self._get_health_check_interval(),
                    )
                )

                async with self._lock:
                    if self._status != PoolStatus.READY:
                        break

                    # Close idle connections
                    now = time.time()
                    idle_timeout = self._get_idle_timeout()

                    # Check available connections
                    i = 0
                    while i < len(self._available):
                        connection = self._available[i]

                        # Skip if we're at min size
                        if len(self._available) - i <= self._get_min_size():
                            i += 1
                            continue

                        # Check if the connection is idle
                        last_use = self._last_validation.get(connection, 0)
                        if now - last_use > idle_timeout:
                            # Remove from available pool
                            self._available.pop(i)

                            # Close the connection
                            try:
                                await self._close_connection(connection)
                            except Exception as e:
                                self.stats.errors += 1
                                self.stats.last_error = e
                                self.stats.last_error_time = time.time()

                            # Remove from pool state
                            if connection in self._creation_time:
                                del self._creation_time[connection]
                            if connection in self._last_validation:
                                del self._last_validation[connection]

                            self.stats.idle_closed += 1
                            self.stats.current_size -= 1
                        else:
                            i += 1

                    # Validate connections that haven't been validated recently
                    validate_interval = self._get_validate_interval()
                    for connection in list(self._available):
                        last_validation = self._last_validation.get(connection, 0)
                        if now - last_validation > validate_interval:
                            is_valid = await self._validate_connection(connection)
                            self._last_validation[connection] = now

                            if not is_valid:
                                # Remove from available pool
                                self._available.remove(connection)

                                # Close the invalid connection
                                try:
                                    await self._close_connection(connection)
                                except Exception as e:
                                    self.stats.errors += 1
                                    self.stats.last_error = e
                                    self.stats.last_error_time = time.time()

                                # Remove from pool state
                                if connection in self._creation_time:
                                    del self._creation_time[connection]
                                if connection in self._last_validation:
                                    del self._last_validation[connection]

                                self.stats.current_size -= 1
            except Exception as e:
                self.stats.errors += 1
                self.stats.last_error = e
                self.stats.last_error_time = time.time()

    def _should_validate(self, connection: T) -> bool:
        """Check if a connection should be validated.

        Args:
            connection: Connection to check

        Returns:
            True if the connection should be validated, False otherwise
        """
        if not self._get_validate_on_acquire():
            return False

        last_validation = self._last_validation.get(connection, 0)
        return time.time() - last_validation > self._get_validate_interval()

    def _is_expired(self, connection: T) -> bool:
        """Check if a connection is expired.

        Args:
            connection: Connection to check

        Returns:
            True if the connection is expired, False otherwise
        """
        creation_time = self._creation_time.get(connection, 0)
        return time.time() - creation_time > self._get_max_lifetime()

    def _get_min_size(self) -> int:
        """Get the minimum pool size.

        Returns:
            Minimum pool size
        """
        return getattr(self.config, "min_size", 1)

    def _get_max_size(self) -> int:
        """Get the maximum pool size.

        Returns:
            Maximum pool size
        """
        return getattr(self.config, "max_size", 10)

    def _get_acquire_timeout(self) -> float:
        """Get the acquire timeout.

        Returns:
            Acquire timeout in seconds
        """
        return getattr(self.config, "acquire_timeout", 10.0)

    def _get_idle_timeout(self) -> float:
        """Get the idle timeout.

        Returns:
            Idle timeout in seconds
        """
        return getattr(self.config, "idle_timeout", 60.0)

    def _get_max_lifetime(self) -> float:
        """Get the maximum connection lifetime.

        Returns:
            Maximum connection lifetime in seconds
        """
        return getattr(self.config, "max_lifetime", 3600.0)

    def _get_validate_on_acquire(self) -> bool:
        """Get whether to validate connections on acquire.

        Returns:
            True if connections should be validated on acquire, False otherwise
        """
        return getattr(self.config, "validate_on_acquire", True)

    def _get_validate_interval(self) -> float:
        """Get the validation interval.

        Returns:
            Validation interval in seconds
        """
        return getattr(self.config, "validate_interval", 30.0)

    def _get_health_check_interval(self) -> float:
        """Get the health check interval.

        Returns:
            Health check interval in seconds
        """
        return getattr(self.config, "health_check_interval", 30.0)

    def _get_retry_attempts(self) -> int:
        """Get the number of retry attempts.

        Returns:
            Number of retry attempts
        """
        return getattr(self.config, "retry_attempts", 3)

    def _get_retry_delay(self) -> float:
        """Get the retry delay.

        Returns:
            Retry delay in seconds
        """
        return getattr(self.config, "retry_delay", 1.0)

    @property
    def status(self) -> PoolStatus:
        """Get the pool status.

        Returns:
            Pool status
        """
        return self._status

    @property
    def size(self) -> int:
        """Get the current pool size.

        Returns:
            Current pool size
        """
        return self.stats.current_size

    @property
    def available(self) -> int:
        """Get the number of available connections.

        Returns:
            Number of available connections
        """
        return len(self._available)

    @property
    def in_use(self) -> int:
        """Get the number of connections in use.

        Returns:
            Number of connections in use
        """
        return self.stats.in_use


# Registry for connection pools
_pools: Dict[str, ConnectionPool] = {}


def register_pool(pool: ConnectionPool) -> None:
    """Register a connection pool.

    Args:
        pool: Connection pool to register

    Raises:
        PepperpyError: If a pool with the same name is already registered
    """
    if pool.name in _pools:
        raise PepperpyError(f"Connection pool '{pool.name}' is already registered")

    _pools[pool.name] = pool


def get_pool(name: str) -> ConnectionPool:
    """Get a connection pool by name.

    Args:
        name: Name of the pool

    Returns:
        Connection pool

    Raises:
        PepperpyError: If the pool is not registered
    """
    if name not in _pools:
        raise PepperpyError(f"Connection pool '{name}' is not registered")

    return _pools[name]


def unregister_pool(name: str) -> None:
    """Unregister a connection pool.

    Args:
        name: Name of the pool

    Raises:
        PepperpyError: If the pool is not registered
    """
    if name not in _pools:
        raise PepperpyError(f"Connection pool '{name}' is not registered")

    del _pools[name]


async def initialize_pools() -> None:
    """Initialize all registered connection pools.

    Raises:
        PepperpyError: If initialization fails
    """
    for pool in _pools.values():
        await pool.initialize()


async def close_pools() -> None:
    """Close all registered connection pools.

    Raises:
        PepperpyError: If closure fails
    """
    for pool in _pools.values():
        await pool.close()


async def get_connection(pool_name: str) -> Any:
    """Get a connection from a pool.

    Args:
        pool_name: Name of the pool

    Returns:
        Connection from the pool

    Raises:
        PepperpyError: If the pool is not registered or a connection cannot be acquired
    """
    pool = get_pool(pool_name)
    return await pool.acquire()


async def release_connection(pool_name: str, connection: Any) -> None:
    """Release a connection back to a pool.

    Args:
        pool_name: Name of the pool
        connection: Connection to release

    Raises:
        PepperpyError: If the pool is not registered or the connection is not in use
    """
    pool = get_pool(pool_name)
    await pool.release(connection)


class PooledResourceContext(Generic[T]):
    """Context manager for pooled resources.

    This context manager acquires a connection from a pool and releases it
    when the context is exited.
    """

    def __init__(self, pool_name: str):
        """Initialize a pooled resource context.

        Args:
            pool_name: Name of the pool
        """
        self.pool_name = pool_name
        self.connection: Optional[T] = None

    async def __aenter__(self) -> T:
        """Enter the context.

        Returns:
            Connection from the pool

        Raises:
            PepperpyError: If a connection cannot be acquired
        """
        self.connection = await get_connection(self.pool_name)
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self.connection is not None:
            await release_connection(self.pool_name, self.connection)
            self.connection = None


def pooled_resource(pool_name: str) -> Callable:
    """Decorator for functions that use pooled resources.

    This decorator wraps a function to acquire a connection from a pool
    and release it when the function returns.

    Args:
        pool_name: Name of the pool

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with PooledResourceContext(pool_name) as connection:
                return await func(connection, *args, **kwargs)

        return wrapper

    return decorator
