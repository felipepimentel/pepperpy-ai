"""
PepperPy Embedding Module.

Module for text embedding operations in the PepperPy framework.
"""

# Results
from pepperpy.embedding.result import EmbeddingResult, SimilarityResult

# Tasks
from pepperpy.embedding.tasks import Embedding, Similarity

__all__ = [
    # Results
    "EmbeddingResult",
    "SimilarityResult",
    # Tasks
    "Embedding",
    "Similarity",
]
