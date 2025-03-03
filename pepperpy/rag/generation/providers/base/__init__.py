"""Base module for generation providers.

This module provides the base classes and interfaces for generation providers.
"""

from pepperpy.rag.generation.providers.base.base import GenerationProvider
from pepperpy.rag.generation.providers.base.registry import (
    get_generation_provider,
    list_generation_providers,
    register_generation_provider,
)
from pepperpy.rag.generation.providers.base.types import (
    GenerationProviderType,
    GenerationRequest,
    GenerationResponse,
)

__all__ = [
    "GenerationProvider",
    "GenerationProviderType",
    "GenerationRequest",
    "GenerationResponse",
    "get_generation_provider",
    "list_generation_providers",
    "register_generation_provider",
]
