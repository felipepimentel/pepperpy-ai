"""Memory store factory."""

from typing import Any, cast

from pepperpy.memory.base import BaseMemoryStore
from pepperpy.memory.config import MemoryStoreConfig, StoreType
from pepperpy.memory.stores.composite import CompositeMemoryStore
from pepperpy.memory.stores.postgres import PostgresMemoryStore
from pepperpy.memory.stores.redis import RedisMemoryStore
from pepperpy.memory.stores.vector import VectorMemoryStore
from pepperpy.monitoring.logger import get_logger

logger = get_logger(__name__)


class StoreError(Exception):
    """Exception raised for errors in store creation."""


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
            if not config.redis_config:
                raise StoreError("Redis configuration is required for Redis store")
            redis_store: RedisMemoryStore = RedisMemoryStore(config.redis_config)
            await redis_store.initialize()
            return cast(BaseMemoryStore[dict[str, Any]], redis_store)

        case StoreType.POSTGRES:
            if not config.postgres_config:
                raise StoreError(
                    "PostgreSQL configuration is required for PostgreSQL store"
                )
            postgres_store: PostgresMemoryStore = PostgresMemoryStore(
                config.postgres_config
            )
            await postgres_store.initialize()
            return cast(BaseMemoryStore[dict[str, Any]], postgres_store)

        case StoreType.VECTOR:
            if not config.vector_config:
                raise StoreError(
                    "Vector store configuration is required for vector store"
                )
            vector_base_store: VectorMemoryStore = VectorMemoryStore(
                config.vector_config
            )
            await vector_base_store.initialize()
            return cast(BaseMemoryStore[dict[str, Any]], vector_base_store)

        case StoreType.COMPOSITE:
            if not config.composite_config:
                raise StoreError(
                    "Composite configuration is required for composite store"
                )

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
                raise StoreError(
                    "Either cache_store or vector_store must be configured"
                )

            composite_store: CompositeMemoryStore = CompositeMemoryStore(
                config.composite_config, primary_store
            )
            await composite_store.initialize()

            # Add the non-primary store if available
            if cache_store and composite_vector_store:
                await composite_store.add_store(
                    composite_vector_store
                    if cache_store == primary_store
                    else cache_store
                )

            return cast(BaseMemoryStore[dict[str, Any]], composite_store)

    # This case should never be reached due to the StoreType validation
    raise StoreError(f"Invalid store type: {store_type}")  # pragma: no cover
