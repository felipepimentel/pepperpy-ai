"""Capability management for the Pepperpy framework.

This module provides a unified interface for managing different types of
capabilities like prompts, search, and memory.

Example:
    >>> from pepperpy.capabilities import PromptCapability, CapabilityMetadata, CapabilityType
    >>> capability = PromptCapability(
    ...     metadata=CapabilityMetadata(
    ...         capability_name="gpt4_prompt",
    ...         capability_type=CapabilityType.PROMPT,
    ...     )
    ... )
    >>> await capability.initialize()
    >>> result = await capability.execute(
    ...     prompt="What is the meaning of life?",
    ...     model="gpt-4",
    ... )
    >>> assert result.success

"""

from .base import (
    BaseCapability,
    CapabilityMetadata,
    CapabilityResult,
    CapabilityState,
    CapabilityType,
)
from .providers import CapabilityProvider
from .types import (
    MemoryCapability,
    PromptCapability,
    SearchCapability,
)

__all__ = [
    # Base types
    "BaseCapability",
    "CapabilityMetadata",
    "CapabilityResult",
    "CapabilityState",
    "CapabilityType",
    # Providers
    "CapabilityProvider",
    # Capability types
    "MemoryCapability",
    "PromptCapability",
    "SearchCapability",
]
