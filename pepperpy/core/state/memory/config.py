"""Memory configuration."""

from enum import Enum
from pathlib import Path
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
    db_schema: str = Field(default="public")
    table: str = Field(default="memory")
    min_connections: int = Field(default=1)
    max_connections: int = Field(default=10)
    ttl: int | None = Field(default=None)


class VectorStoreConfig(BaseConfig):
    """Vector store configuration model."""

    store_type: StoreType = Field(default=StoreType.VECTOR)
    model_name: str = Field(default="all-MiniLM-L6-v2")
    storage_path: Path | None = Field(default=None)
    redis_config: RedisConfig | None = Field(default=None)
    postgres_config: PostgresConfig | None = Field(default=None)
    dimension: int = Field(default=1536)  # Default for OpenAI embeddings
    similarity_threshold: float = Field(default=0.8)
    max_results: int = Field(default=10)


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

    def model_post_init(self, __context: Any) -> None:
        """Validate configuration after initialization."""
        super().model_post_init(__context)
        # Skip validation for default values
        if all(
            config is None
            for config in [
                self.redis_config,
                self.postgres_config,
                self.vector_config,
                self.composite_config,
            ]
        ):
            return

        if self.store_type == StoreType.REDIS:
            if not self.redis_config:
                raise ValueError("Redis configuration is required for Redis store")
            if self.postgres_config:
                raise ValueError(
                    "Postgres configuration cannot be used with Redis store"
                )
            if self.vector_config:
                raise ValueError("Vector configuration cannot be used with Redis store")
            if self.composite_config:
                raise ValueError(
                    "Composite configuration cannot be used with Redis store"
                )
        elif self.store_type == StoreType.POSTGRES:
            if not self.postgres_config:
                raise ValueError(
                    "Postgres configuration is required for Postgres store"
                )
            if self.redis_config:
                raise ValueError(
                    "Redis configuration cannot be used with Postgres store"
                )
            if self.vector_config:
                raise ValueError(
                    "Vector configuration cannot be used with Postgres store"
                )
            if self.composite_config:
                raise ValueError(
                    "Composite configuration cannot be used with Postgres store"
                )
        elif self.store_type == StoreType.VECTOR:
            if not self.vector_config:
                raise ValueError("Vector configuration is required for Vector store")
            if self.redis_config:
                raise ValueError("Redis configuration cannot be used with Vector store")
            if self.postgres_config:
                raise ValueError(
                    "Postgres configuration cannot be used with Vector store"
                )
            if self.composite_config:
                raise ValueError(
                    "Composite configuration cannot be used with Vector store"
                )
        elif self.store_type == StoreType.COMPOSITE:
            if not self.composite_config:
                raise ValueError(
                    "Composite configuration is required for Composite store"
                )
            if self.redis_config:
                raise ValueError(
                    "Redis configuration cannot be used with Composite store"
                )
            if self.postgres_config:
                raise ValueError(
                    "Postgres configuration cannot be used with Composite store"
                )
            if self.vector_config:
                raise ValueError(
                    "Vector configuration cannot be used with Composite store"
                )


class MemoryConfig(BaseConfig):
    """Memory store configuration."""

    type: StoreType = Field(default=StoreType.REDIS)  # type: ignore[assignment]
    parameters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


# Update forward references
CompositeStoreConfig.model_rebuild()
MemoryStoreConfig.model_rebuild()
