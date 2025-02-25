"""Type definitions for the caching system."""

from typing import Any, Optional, TypeVar, Union

# Type variable for cache values
CacheValueType = TypeVar("CacheValueType")

# Type alias for cache metadata
CacheMetadata = dict[str, Any]

# Type alias for cache key
CacheKey = Union[str, bytes]

# Type alias for cache TTL
CacheTTL = Optional[int]

# Type alias for cache size
CacheSize = Optional[int]

# Type alias for cache stats
CacheStats = dict[str, int | float]

__all__ = [
    "CacheKey",
    "CacheMetadata",
    "CacheSize",
    "CacheStats",
    "CacheTTL",
    "CacheValueType",
]
