"""Tests for memory store factory."""

from unittest.mock import AsyncMock, patch

import pytest

from pepperpy.memory.config import (
    CompositeStoreConfig,
    MemoryStoreConfig,
    PostgresConfig,
    RedisConfig,
    StoreType,
    VectorStoreConfig,
)
from pepperpy.memory.factory import (
    StoreError,
    _create_composite_store,
    _create_postgres_store,
    _create_redis_store,
    _create_vector_store,
    create_store,
)
from pepperpy.memory.stores.composite import CompositeMemoryStore
from pepperpy.memory.stores.postgres import PostgresMemoryStore
from pepperpy.memory.stores.redis import RedisMemoryStore
from pepperpy.memory.stores.vector import VectorMemoryStore


@pytest.mark.asyncio
async def test_create_redis_store():
    """Test Redis store creation."""
    # Test successful creation
    config = MemoryStoreConfig(
        store_type=StoreType.REDIS,
        redis_config=RedisConfig(
            host="localhost",
            port=6379,
        ),
    )
    with patch.object(RedisMemoryStore, "initialize", AsyncMock()):
        store = await _create_redis_store(config)
        assert isinstance(store, RedisMemoryStore)
        assert store.initialize.called  # type: ignore

    # Test missing Redis config
    config = MemoryStoreConfig(store_type=StoreType.REDIS)
    with pytest.raises(StoreError, match="Redis configuration is required"):
        await _create_redis_store(config)


@pytest.mark.asyncio
async def test_create_postgres_store():
    """Test PostgreSQL store creation."""
    # Test successful creation
    config = MemoryStoreConfig(
        store_type=StoreType.POSTGRES,
        postgres_config=PostgresConfig(
            host="localhost",
            port=5432,
            database="test_db",
        ),
    )
    with patch.object(PostgresMemoryStore, "initialize", AsyncMock()):
        store = await _create_postgres_store(config)
        assert isinstance(store, PostgresMemoryStore)
        assert store.initialize.called  # type: ignore

    # Test missing PostgreSQL config
    config = MemoryStoreConfig(store_type=StoreType.POSTGRES)
    with pytest.raises(StoreError, match="PostgreSQL configuration is required"):
        await _create_postgres_store(config)


@pytest.mark.asyncio
async def test_create_vector_store():
    """Test vector store creation."""
    # Test successful creation
    config = MemoryStoreConfig(
        store_type=StoreType.VECTOR,
        vector_config=VectorStoreConfig(
            model_name="test-model",
        ),
    )
    with patch.object(VectorMemoryStore, "initialize", AsyncMock()):
        store = await _create_vector_store(config)
        assert isinstance(store, VectorMemoryStore)
        assert store.initialize.called  # type: ignore

    # Test missing vector config
    config = MemoryStoreConfig(store_type=StoreType.VECTOR)
    with pytest.raises(StoreError, match="Vector store configuration is required"):
        await _create_vector_store(config)


@pytest.mark.asyncio
async def test_create_composite_store():
    """Test composite store creation."""
    # Test successful creation with cache store
    cache_config = MemoryStoreConfig(
        store_type=StoreType.REDIS,
        redis_config=RedisConfig(host="localhost"),
    )
    vector_config = VectorStoreConfig(
        model_name="test-model",
    )
    config = MemoryStoreConfig(
        store_type=StoreType.COMPOSITE,
        composite_config=CompositeStoreConfig(
            cache_store=cache_config,
            vector_store=vector_config,
        ),
    )

    with (
        patch.object(RedisMemoryStore, "initialize", AsyncMock()),
        patch.object(VectorMemoryStore, "initialize", AsyncMock()),
        patch.object(CompositeMemoryStore, "initialize", AsyncMock()),
        patch.object(CompositeMemoryStore, "add_store", AsyncMock()),
    ):
        store = await _create_composite_store(config)
        assert isinstance(store, CompositeMemoryStore)
        assert store.initialize.called  # type: ignore
        assert store.add_store.called  # type: ignore

    # Test missing composite config
    config = MemoryStoreConfig(store_type=StoreType.COMPOSITE)
    with pytest.raises(StoreError, match="Composite configuration is required"):
        await _create_composite_store(config)

    # Test missing both cache and vector stores
    config = MemoryStoreConfig(
        store_type=StoreType.COMPOSITE,
        composite_config=CompositeStoreConfig(),
    )
    with pytest.raises(
        StoreError, match="Either cache_store or vector_store must be configured"
    ):
        await _create_composite_store(config)


@pytest.mark.asyncio
async def test_create_store():
    """Test store creation factory."""
    # Test Redis store creation
    config = MemoryStoreConfig(
        store_type=StoreType.REDIS,
        redis_config=RedisConfig(host="localhost"),
    )
    with patch(
        "pepperpy.memory.factory._create_redis_store", AsyncMock()
    ) as mock_redis:
        await create_store(config)
        assert mock_redis.called

    # Test PostgreSQL store creation
    config = MemoryStoreConfig(
        store_type=StoreType.POSTGRES,
        postgres_config=PostgresConfig(host="localhost"),
    )
    with patch(
        "pepperpy.memory.factory._create_postgres_store", AsyncMock()
    ) as mock_postgres:
        await create_store(config)
        assert mock_postgres.called

    # Test vector store creation
    config = MemoryStoreConfig(
        store_type=StoreType.VECTOR,
        vector_config=VectorStoreConfig(model_name="test-model"),
    )
    with patch(
        "pepperpy.memory.factory._create_vector_store", AsyncMock()
    ) as mock_vector:
        await create_store(config)
        assert mock_vector.called

    # Test composite store creation
    config = MemoryStoreConfig(
        store_type=StoreType.COMPOSITE,
        composite_config=CompositeStoreConfig(
            cache_store=MemoryStoreConfig(
                store_type=StoreType.REDIS,
                redis_config=RedisConfig(host="localhost"),
            ),
        ),
    )
    with patch(
        "pepperpy.memory.factory._create_composite_store", AsyncMock()
    ) as mock_composite:
        await create_store(config)
        assert mock_composite.called

    # Test invalid store type
    config = MemoryStoreConfig(store_type="nonexistent_store_type")  # type: ignore
    with pytest.raises(StoreError, match="Invalid store type"):
        await create_store(config)
