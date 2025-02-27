"""Sistema de cache para reduzir chamadas repetidas à API."""

from .cache import Cache, CacheEntry
from .manager import CacheManager
from .policy import CachePolicy

__all__ = [
    "Cache",
    "CacheEntry",
    "CacheManager",
    "CachePolicy",
]
