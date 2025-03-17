"""Connection pool functionality for PepperPy.

This module provides connection pooling functionality for the PepperPy framework.
It re-exports the connection pooling functionality from pepperpy.infra.connection.
"""

from typing import Any, Dict, Optional, Type, TypeVar

from pepperpy.core.errors import PepperPyError
from pepperpy.infra.connection import (
    ConnectionPool,
    ConnectionPoolConfig,
    PoolStatus,
    close_pools,
    get_pool,
    initialize_pools,
    pooled_resource,
    register_pool,
    release_connection,
    unregister_pool,
)

T = TypeVar("T")
C = TypeVar("C", bound=ConnectionPoolConfig)

__all__ = [
    "ConnectionPool",
    "ConnectionPoolConfig",
    "PoolStatus",
    "close_pools",
    "get_pool",
    "initialize_pools",
    "pooled_resource",
    "register_pool",
    "release_connection",
    "unregister_pool",
] 