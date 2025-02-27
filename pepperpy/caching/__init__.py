"""Unified caching system for PepperPy.

This module provides a comprehensive caching system for all PepperPy components,
with specialized implementations for different use cases:

- Base caching functionality (base.py)
  - Common interfaces
  - Serialization
  - Entry management

- Memory caching (memory.py)
  - In-memory storage
  - LRU/TTL policies
  - Thread-safe operations

- Distributed caching (distributed.py)
  - Redis backend
  - Cluster support
  - Pub/sub capabilities

- Vector caching (vector.py)
  - Optimized for embeddings
  - Similarity-based eviction
  - Batch operations

- Migration utilities (migration.py)
  - Data migration from old caches
  - Configuration conversion
  - Usage pattern adaptation

This unified system replaces the previous fragmented implementations:
- memory/cache.py (agent-specific cache)
- core/resources/cache.py (resource cache)
- optimization/caching/ (performance cache)
- rag/vector/optimization/caching.py (vector cache)

All components should use this module for caching needs, with appropriate
specialization for their specific requirements.
"""

from typing import Dict, List, Optional, Type, Union

from .base import (
    BackendError,
    Cache,
    CacheBackend,
    CacheEntry,
    CacheError,
    CachePolicy,
    CachePolicyType,
    PickleSerializer,
    PolicyError,
    SerializationError,
    Serializer,
)
from .distributed import DistributedCache, RedisCache
from .memory import (
    FIFOPolicy,
    LFUPolicy,
    LRUPolicy,
    MemoryCache,
    RandomPolicy,
)
from .migration import MigrationHelper
from .vector import VectorCache

__all__ = [
    # Base classes
    "Cache",
    "CacheBackend",
    "CacheEntry",
    "CacheError",
    "CachePolicy",
    "CachePolicyType",
    "Serializer",
    "PickleSerializer",
    "SerializationError",
    "BackendError",
    "PolicyError",
    # Implementations
    "MemoryCache",
    "LRUPolicy",
    "LFUPolicy",
    "FIFOPolicy",
    "RandomPolicy",
    "DistributedCache",
    "RedisCache",
    "VectorCache",
    # Utilities
    "MigrationHelper",
]
