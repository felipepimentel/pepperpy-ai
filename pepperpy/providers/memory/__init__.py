"""Memory providers for pepperpy.

This module contains memory providers for pepperpy, including:
- Redis memory provider
- PostgreSQL memory provider
"""

from typing import Dict, Type

from pepperpy.memory.base import MemoryProvider

# Registry of available memory providers
MEMORY_PROVIDERS: Dict[str, Type[MemoryProvider]] = {}


def register_memory_provider(name: str, provider: Type[MemoryProvider]) -> None:
    """Register a memory provider.

    Args:
        name: Provider name
        provider: Provider class
    """
    MEMORY_PROVIDERS[name] = provider


__all__ = [
    "register_memory_provider",
    "MEMORY_PROVIDERS",
]
