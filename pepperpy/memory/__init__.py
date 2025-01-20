"""Memory module for Pepperpy."""

from .base import BaseMemory, MemoryBackend
from .backends.memory import InMemoryBackend
from .backends.redis import RedisBackend
from .long_term.storage import LongTermStorage
from .long_term.retriever import LongTermRetriever
from .short_term.context import ContextMemory
from .short_term.session import SessionMemory
from .memory_manager import MemoryManager
from .vector_support import VectorSupport, VectorError

__all__ = [
    # Base components
    "BaseMemory",
    "MemoryBackend",
    # Memory backends
    "InMemoryBackend",
    "RedisBackend",
    # Short-term memory
    "ContextMemory",
    "SessionMemory",
    # Long-term memory
    "LongTermStorage",
    "LongTermRetriever",
    # Memory manager
    "MemoryManager",
    # Vector support
    "VectorSupport",
    "VectorError",
]
