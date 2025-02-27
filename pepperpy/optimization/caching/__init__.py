"""General cache for performance optimization.

This module implements a cache system for general performance optimization,
focusing on:

- Data Cache
  - Computation results
  - Frequent data
  - External resources
  - Common queries

- General Features
  - Expiration policy
  - Size limit
  - Persistence
  - Distribution

This cache is different from the agent cache (pepperpy/memory/cache.py)
as it focuses on:
- Optimizing general performance
- Reducing resource load
- Minimizing latency
- Saving bandwidth

The module provides:
- Local cache
- Distributed cache
- Configurable policies
- Performance metrics
"""

from typing import Dict, List, Optional, Union

from .distributed import DistributedCache
from .local import LocalCache
from .policy import CachePolicy

__version__ = "0.1.0"
__all__ = [
    "LocalCache",
    "DistributedCache",
    "CachePolicy",
]
