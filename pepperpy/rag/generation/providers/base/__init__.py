"""Base module for generation providers.

This module provides the base classes and interfaces for generation providers.
"""

from pepperpy.rag.generation.providers.base.base import GenerationProvider
from pepperpy.rag.generation.providers.base.registry import (
    register_generation_provider,
    get_generation_provider,
    list_generation_providers,
)
from pepperpy.rag.generation.providers.base.types import (
    GenerationProviderType,
    GenerationRequest,
    GenerationResponse,
)

__all__ = [
    "GenerationProvider",
    "register_generation_provider",
    "get_generation_provider",
    "list_generation_providers",
    "GenerationProviderType",
    "GenerationRequest",
    "GenerationResponse",
]