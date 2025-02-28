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


class QualityPruner(VectorPruner):
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


class RedundancyPruner(VectorPruner):
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


class DiversityPruner(VectorPruner):
    """Prune vectors to maintain diversity."""

    def __init__(self, similarity_threshold: float = 0.9) -> None:
        """Initialize diversity pruner.

        Args:
            similarity_threshold: Threshold for considering vectors similar
        """
        self.similarity_threshold = similarity_threshold

    def prune(self, vectors: NDArray, scores: NDArray) -> Tuple[NDArray, NDArray]:
        """Prune similar vectors, keeping those with higher scores.

        Args:
            vectors: Vectors to prune (n_vectors, n_dimensions)
            scores: Importance scores for each vector

        Returns:
            Tuple of (pruned_vectors, kept_indices)
        """
        # Normalize vectors for cosine similarity
        normalized = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

        # Compute pairwise similarities
        similarities = np.dot(normalized, normalized.T)

        # Sort indices by score (descending)
        sorted_idx = np.argsort(scores)[::-1]

        # Keep track of which indices to keep
        keep = np.ones(len(vectors), dtype=bool)

        # Process vectors in order of decreasing score
        for i in range(len(sorted_idx)):
            idx = sorted_idx[i]

            # Skip if already marked for removal
            if not keep[idx]:
                continue

            # Find similar vectors
            similar = similarities[idx] > self.similarity_threshold

            # Don't remove the current vector
            similar[idx] = False

            # Mark similar vectors for removal
            keep = keep & ~similar

        # Get indices to keep
        keep_idx = np.where(keep)[0]

        # Return pruned vectors and indices
        return vectors[keep_idx], keep_idx
