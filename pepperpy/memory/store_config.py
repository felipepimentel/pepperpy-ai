"""Memory store configuration.

This file has been deprecated in favor of pepperpy/memory/config.py.
Please update your imports to use the new location.
"""

from pepperpy.memory.config import (
    CompositeStoreConfig,
    MemoryConfig,
    PostgresConfig,
    RedisConfig,
    VectorStoreConfig,
)

__all__ = [
    "CompositeStoreConfig",
    "MemoryConfig",
    "PostgresConfig",
    "RedisConfig",
    "VectorStoreConfig",
]
