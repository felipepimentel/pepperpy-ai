"""Vector pruning for index optimization.

Implements pruning techniques to reduce index size
while maintaining search quality.
"""

from typing import Tuple

import numpy as np
from numpy.typing import NDArray


class VectorPruner:
    """Base class for vector pruning."""

    def prune(self, vectors: NDArray, scores: NDArray) -> Tuple[NDArray, NDArray]:
        """Prune vectors based on scores.

        Args:
            vectors: Vectors to prune (n_vectors, n_dimensions)
            scores: Importance scores for each vector

        Returns:
            Tuple of (pruned_vectors, kept_indices)
        """
        raise NotImplementedError


class ThresholdPruner(VectorPruner):
    """Prune vectors based on score threshold."""

    def __init__(self, threshold: float) -> None:
        """Initialize threshold pruner.

        Args:
            threshold: Score threshold for pruning
        """
        self.threshold = threshold

    def prune(self, vectors: NDArray, scores: NDArray) -> Tuple[NDArray, NDArray]:
        """Prune vectors with scores below threshold.

        Args:
            vectors: Vectors to prune (n_vectors, n_dimensions)
            scores: Importance scores for each vector

        Returns:
            Tuple of (pruned_vectors, kept_indices)
        """
        # Find indices to keep
        keep_idx = np.where(scores >= self.threshold)[0]

        # Return pruned vectors and indices
        return vectors[keep_idx], keep_idx


class TopKPruner(VectorPruner):
    """Keep top K vectors by score."""

    def __init__(self, k: int) -> None:
        """Initialize top-K pruner.

        Args:
            k: Number of vectors to keep
        """
        self.k = k

    def prune(self, vectors: NDArray, scores: NDArray) -> Tuple[NDArray, NDArray]:
        """Keep top K vectors by score.

        Args:
            vectors: Vectors to prune (n_vectors, n_dimensions)
            scores: Importance scores for each vector

        Returns:
            Tuple of (pruned_vectors, kept_indices)
        """
        # Get indices of top K scores
        top_k_idx = np.argsort(scores)[-self.k :]

        # Return pruned vectors and indices
        return vectors[top_k_idx], top_k_idx
