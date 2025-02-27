"""RAG augmentation package.

This package provides functionality for augmenting RAG inputs and outputs,
including query expansion, context enrichment, and result refinement.
"""

from .augmenters import (
    Augmenter,
    QueryAugmenter,
    ResultAugmenter,
    ContextAugmenter,
)

__all__ = [
    # Base class
    "Augmenter",
    # Specific augmenters
    "QueryAugmenter",
    "ResultAugmenter",
    "ContextAugmenter",
]