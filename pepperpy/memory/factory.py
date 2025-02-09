"""Memory store factory."""

from typing import Any, cast

from pepperpy.memory.base import BaseMemoryStore
from pepperpy.memory.config import MemoryConfig, MemoryStoreConfig, StoreType
from pepperpy.memory.stores.composite import CompositeMemoryStore
from pepperpy.memory.stores.postgres import PostgresMemoryStore
from pepperpy.memory.stores.redis import RedisMemoryStore
from pepperpy.memory.stores.vector import VectorMemoryStore
from pepperpy.monitoring.logger import get_logger

logger = get_logger(__name__)


class StoreError(Exception):
    """Exception raised for errors in store creation."""


async def _create_redis_store(
    config: MemoryStoreConfig,
) -> BaseMemoryStore[dict[str, Any]]:
    """Create a Redis memory store.

    Args:
        config: Memory store configuration.

    Returns:
        BaseMemoryStore: Configured Redis store instance.

    Raises:
        StoreError: If Redis configuration is missing.
    """
    if not config.redis_config:
        raise StoreError("Redis configuration is required for Redis store")
    redis_store: RedisMemoryStore[dict[str, Any]] = RedisMemoryStore[dict[str, Any]](
        config.redis_config
    )
    await redis_store.initialize()
    return cast(BaseMemoryStore[dict[str, Any]], redis_store)


async def _create_postgres_store(
    config: MemoryStoreConfig,
) -> BaseMemoryStore[dict[str, Any]]:
    """Create a PostgreSQL memory store.

    Args:
        config: Memory store configuration.

    Returns:
        BaseMemoryStore: Configured PostgreSQL store instance.

    Raises:
        StoreError: If PostgreSQL configuration is missing.
    """
    if not config.postgres_config:
        raise StoreError("PostgreSQL configuration is required for PostgreSQL store")

    # Construct DSN string from config
    dsn = f"postgresql://{config.postgres_config.user}:{config.postgres_config.password}@{config.postgres_config.host}:{config.postgres_config.port}/{config.postgres_config.database}"

    postgres_store: PostgresMemoryStore[dict[str, Any]] = PostgresMemoryStore[
        dict[str, Any]
    ](
        name="postgres",  # Use a default name since it's required
        dsn=dsn,
        schema=config.postgres_config.db_schema,
        table=config.postgres_config.table,
    )
    await postgres_store.initialize()
    return cast(BaseMemoryStore[dict[str, Any]], postgres_store)


async def _create_vector_store(
    config: MemoryStoreConfig,
) -> BaseMemoryStore[dict[str, Any]]:
    """Create a vector memory store.

    Args:
        config: Memory store configuration.

    Returns:
        BaseMemoryStore: Configured vector store instance.

    Raises:
        StoreError: If vector store configuration is missing.
    """
    if not config.vector_config:
        raise StoreError("Vector store configuration is required for vector store")
    vector_store: VectorMemoryStore = VectorMemoryStore(config.vector_config)
    await vector_store.initialize()
    return cast(BaseMemoryStore[dict[str, Any]], vector_store)


async def _create_composite_store(
    config: MemoryStoreConfig,
) -> BaseMemoryStore[dict[str, Any]]:
    """Create a composite memory store.

    Args:
        config: Memory store configuration.

    Returns:
        BaseMemoryStore: Configured composite store instance.

    Raises:
        StoreError: If composite configuration is missing or invalid.
    """
    if not config.composite_config:
        raise StoreError("Composite configuration is required for composite store")

    # Create cache store if configured
    cache_store: BaseMemoryStore[dict[str, Any]] | None = None
    if config.composite_config.cache_store:
        cache_store = await create_store(config.composite_config.cache_store)

    # Create vector store if configured
    composite_vector_store: BaseMemoryStore[dict[str, Any]] | None = None
    if config.composite_config.vector_store:
        composite_vector_store = await create_store(
            MemoryStoreConfig(
                store_type=StoreType.VECTOR,
                vector_config=config.composite_config.vector_store,
            )
        )

    # Choose primary store:
    # - Use cache store if available
    # - Otherwise use vector store
    primary_store = cache_store if cache_store else composite_vector_store
    if not primary_store:
        raise StoreError("Either cache_store or vector_store must be configured")

    # Create memory config for composite store
    memory_config = MemoryConfig(
        type=StoreType.COMPOSITE,
        parameters={
            "cache_store": config.composite_config.cache_store.dict()
            if config.composite_config.cache_store
            else None,
            "vector_store": config.composite_config.vector_store.dict()
            if config.composite_config.vector_store
            else None,
        },
        metadata={},
    )

    composite_store: CompositeMemoryStore[dict[str, Any]] = CompositeMemoryStore[
        dict[str, Any]
    ](
        config=memory_config,
        primary_store=primary_store,
    )
    await composite_store.initialize()

    # Add the non-primary store if available
    if cache_store and composite_vector_store:
        await composite_store.add_store(
            composite_vector_store if cache_store == primary_store else cache_store
        )

    return cast(BaseMemoryStore[dict[str, Any]], composite_store)


async def create_store(config: MemoryStoreConfig) -> BaseMemoryStore[dict[str, Any]]:
    """Create a memory store based on configuration.

    Args:
        config: Memory store configuration.

    Returns:
        BaseMemoryStore: Configured memory store instance.

    Raises:
        StoreError: If store creation fails due to invalid configuration.
    """
    try:
        store_type = StoreType(config.store_type)
    except ValueError as e:
        raise StoreError(f"Invalid store type: {config.store_type}") from e

    match store_type:
        case StoreType.REDIS:
            return await _create_redis_store(config)
        case StoreType.POSTGRES:
            return await _create_postgres_store(config)
        case StoreType.VECTOR:
            return await _create_vector_store(config)
        case StoreType.COMPOSITE:
            return await _create_composite_store(config)

    # This case should never be reached due to the StoreType validation
    raise StoreError(f"Invalid store type: {store_type}")  # pragma: no cover
