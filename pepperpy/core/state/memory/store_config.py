"""Memory store configuration module.

This module provides configuration classes for different memory store backends.
"""

from typing import Optional

from pydantic import BaseModel, Field


class PostgresConfig(BaseModel):
    """Configuration for PostgreSQL memory store.

    Attributes
    ----------
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
        schema: Database schema
        table: Database table
        ssl_mode: SSL mode
        ssl_cert: SSL certificate path
    """

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="pepperpy")
    user: str = Field(default="postgres")
    password: str = Field(default="")
    schema: str = Field(default="public")
    table: str = Field(default="memory")
    ssl_mode: Optional[str] = Field(default=None)
    ssl_cert: Optional[str] = Field(default=None)


class RedisConfig(BaseModel):
    """Configuration for Redis memory store.

    Attributes
    ----------
        host: Redis host
        port: Redis port
        db: Redis database number
        password: Redis password
        ssl: Whether to use SSL
        ssl_cert: SSL certificate path
    """

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: Optional[str] = Field(default=None)
    ssl: bool = Field(default=False)
    ssl_cert: Optional[str] = Field(default=None)


class FileConfig(BaseModel):
    """Configuration for file-based memory store.

    Attributes
    ----------
        path: Base path for storing files
        format: File format (json, pickle, etc.)
        compress: Whether to compress files
    """

    path: str = Field(default="./memory")
    format: str = Field(default="json")
    compress: bool = Field(default=False)
