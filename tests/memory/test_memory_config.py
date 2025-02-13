"""Tests for memory configuration."""

import pytest
from pydantic import ValidationError

from pepperpy.memory.config import (
    CompositeStoreConfig,
    MemoryConfig,
    MemoryStoreConfig,
    PostgresConfig,
    RedisConfig,
    StoreType,
    VectorStoreConfig,
)


def test_memory_store_config():
    """Test memory store configuration."""
    # Test valid configuration with Redis
    config = MemoryStoreConfig(
        store_type=StoreType.REDIS,
        redis_config=RedisConfig(
            host="localhost",
            port=6379,
            ttl=3600,
        ),
    )
    assert config.store_type == StoreType.REDIS
    assert config.redis_config is not None
    assert config.redis_config.host == "localhost"
    assert config.redis_config.port == 6379
    assert config.redis_config.ttl == 3600

    # Test valid configuration with Postgres
    config = MemoryStoreConfig(
        store_type=StoreType.POSTGRES,
        postgres_config=PostgresConfig(
            host="localhost",
            port=5432,
            database="test_db",
        ),
    )
    assert config.store_type == StoreType.POSTGRES
    assert config.postgres_config is not None
    assert config.postgres_config.host == "localhost"
    assert config.postgres_config.port == 5432
    assert config.postgres_config.database == "test_db"

    # Test default values
    config = MemoryStoreConfig()
    assert config.store_type == StoreType.REDIS
    assert config.redis_config is None
    assert config.postgres_config is None
    assert config.vector_config is None
    assert config.composite_config is None

    # Test invalid store type
    with pytest.raises(ValidationError):
        MemoryStoreConfig(store_type="nonexistent_store_type")  # type: ignore

    # Test missing config for store type
    with pytest.raises(ValidationError):
        MemoryStoreConfig(store_type=StoreType.POSTGRES)  # Missing postgres_config


def test_memory_config():
    """Test memory configuration."""
    # Test valid configuration
    config = MemoryConfig(
        type=StoreType.REDIS,
        parameters={
            "host": "localhost",
            "port": 6379,
            "ttl": 3600,
        },
        metadata={
            "version": "1.0",
            "description": "Test config",
        },
    )
    assert config.type == StoreType.REDIS
    assert config.parameters["host"] == "localhost"
    assert config.parameters["port"] == 6379
    assert config.metadata["version"] == "1.0"

    # Test default values
    config = MemoryConfig()
    assert config.type == StoreType.REDIS
    assert config.parameters == {}
    assert config.metadata == {}

    # Test invalid type
    with pytest.raises(ValidationError):
        MemoryConfig(type="nonexistent_store_type")  # type: ignore


def test_composite_store_config():
    """Test composite store configuration."""
    # Test valid configuration
    cache_store = MemoryStoreConfig(
        store_type=StoreType.REDIS,
        redis_config=RedisConfig(host="localhost"),
    )
    vector_store = VectorStoreConfig(
        store_type=StoreType.VECTOR,
        model_name="test-model",
    )
    config = CompositeStoreConfig(
        store_type=StoreType.COMPOSITE,
        cache_store=cache_store,
        vector_store=vector_store,
    )
    assert config.store_type == StoreType.COMPOSITE
    assert config.cache_store == cache_store
    assert config.vector_store == vector_store

    # Test default values
    config = CompositeStoreConfig()
    assert config.store_type == StoreType.COMPOSITE
    assert config.cache_store is None
    assert config.vector_store is None


def test_config_validation():
    """Test configuration validation."""
    # Test invalid redis configuration
    with pytest.raises(ValidationError):
        MemoryStoreConfig(
            store_type=StoreType.REDIS,
            redis_config=RedisConfig(port="invalid"),  # type: ignore
        )

    # Test invalid postgres configuration
    with pytest.raises(ValidationError):
        MemoryStoreConfig(
            store_type=StoreType.POSTGRES,
            postgres_config=PostgresConfig(port="invalid"),  # type: ignore
        )

    # Test mismatched store type and config
    with pytest.raises(ValidationError):
        MemoryStoreConfig(
            store_type=StoreType.REDIS,
            postgres_config=PostgresConfig(),  # Should be redis_config
        )
