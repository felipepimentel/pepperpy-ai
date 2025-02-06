"""Memory configuration."""

from enum import Enum
from typing import Any, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field


class StoreType(str, Enum):
    """Store type enum."""

    REDIS = "redis"
    POSTGRES = "postgres"
    VECTOR = "vector"
    COMPOSITE = "composite"


T = TypeVar("T", bound="BaseConfig")


class BaseConfig(BaseModel):
    """Base configuration model."""

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        str_to_lower=True,
        use_enum_values=True,
    )  # type: ignore[assignment, misc]


class RedisConfig(BaseConfig):
    """Redis configuration model."""

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: str | None = Field(default=None)
    username: str | None = Field(default=None)
    ssl: bool = Field(default=False)
    ssl_ca_certs: str | None = Field(default=None)
    ssl_certfile: str | None = Field(default=None)
    ssl_keyfile: str | None = Field(default=None)
    ssl_cert_reqs: str | None = Field(default=None)
    prefix: str = Field(default="memory")
    ttl: int | None = Field(default=None)
    extra_args: dict[str, Any] = Field(default_factory=dict)


class PostgresConfig(BaseConfig):
    """PostgreSQL configuration model."""

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    database: str = Field(default="pepperpy")
    schema: str = Field(default="public")
    table: str = Field(default="memory")
    min_connections: int = Field(default=1)
    max_connections: int = Field(default=10)
    ttl: int | None = Field(default=None)


class VectorStoreConfig(BaseConfig):
    """Vector store configuration model."""

    store_type: StoreType = Field(default=StoreType.REDIS)
    redis_config: RedisConfig | None = Field(default=None)
    postgres_config: PostgresConfig | None = Field(default=None)


class CompositeStoreConfig(BaseConfig):
    """Composite store configuration model."""

    store_type: StoreType = Field(default=StoreType.COMPOSITE)
    cache_store: Union["MemoryStoreConfig", None] = Field(default=None)
    vector_store: VectorStoreConfig | None = Field(default=None)


class MemoryStoreConfig(BaseConfig):
    """Memory store configuration model."""

    store_type: StoreType = Field(default=StoreType.REDIS)
    redis_config: RedisConfig | None = Field(default=None)
    postgres_config: PostgresConfig | None = Field(default=None)
    vector_config: VectorStoreConfig | None = Field(default=None)
    composite_config: CompositeStoreConfig | None = Field(default=None)


class MemoryConfig(BaseConfig):
    """Memory store configuration."""

    type: StoreType = Field(default=StoreType.REDIS)  # type: ignore[assignment]
    parameters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


# Update forward references
CompositeStoreConfig.model_rebuild()
MemoryStoreConfig.model_rebuild()
