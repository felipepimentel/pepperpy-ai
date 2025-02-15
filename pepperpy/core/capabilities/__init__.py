"""Core capabilities management module.

This module provides a unified system for managing agent capabilities,
including error handling, type definitions, and common functionality.
"""

from .base import Capability, CapabilityContext, CapabilityResult
from .errors import (
    AnalysisError,
    CapabilityError,
    CapabilityType,
    GenerationError,
    LearningError,
    MemoryError,
    PerceptionError,
    PlanningError,
    ReasoningError,
)
from .registry import CapabilityRegistry

# Create global registry instance
registry = CapabilityRegistry()

__all__ = [
    "Capability",
    "CapabilityContext",
    "CapabilityResult",
    "CapabilityRegistry",
    "registry",
    # Error types
    "CapabilityError",
    "CapabilityType",
    "AnalysisError",
    "GenerationError",
    "LearningError",
    "MemoryError",
    "PerceptionError",
    "PlanningError",
    "ReasoningError",
]
