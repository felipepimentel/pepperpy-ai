"""Architecture management and validation.

This module provides tools for managing and validating architectural patterns.
"""

from pepperpy.core.architecture.evolution import EvolutionManager, EvolutionRecord
from pepperpy.core.architecture.validator import (
    ArchitectureRule,
    ArchitectureValidator,
    ValidationResult,
)

__all__ = [
    # Evolution management
    "EvolutionManager",
    "EvolutionRecord",
    # Validation
    "ArchitectureRule",
    "ArchitectureValidator",
    "ValidationResult",
]
