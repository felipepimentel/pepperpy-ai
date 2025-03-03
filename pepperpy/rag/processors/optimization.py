"""Vector optimization techniques for RAG systems.

This module provides implementations for:
1. Vector compression to reduce memory usage
2. Vector pruning to reduce index size

Both techniques aim to optimize RAG systems while maintaining search quality.
"""

from typing import Optional, Tuple

import numpy as np
from numpy.typing import NDArray

#
# Vector Compression
#


class VectorCompressor:
    """Base class for vector compression."""

    def compress(self, vectors: NDArray) -> NDArray:
        """Compress vectors.

        Args:
            vectors: Vectors to compress (n_vectors, n_dimensions)

        Returns:
            Compressed vectors

        """
        raise NotImplementedError

    def decompress(self, compressed: NDArray) -> NDArray:
        """Decompress vectors.

        Args:
            compressed: Compressed vectors

        Returns:
            Original vectors

        """
        raise NotImplementedError


class DimensionalityReducer(VectorCompressor):
    """PCA-based vector compression."""

    def __init__(self, n_components: int) -> None:
        """Initialize PCA compressor.

        Args:
            n_components: Number of components to keep

        """
        self.n_components = n_components
        self._components: Optional[NDArray] = None
        self._mean: Optional[NDArray] = None

    def compress(self, vectors: NDArray) -> NDArray:
        """Compress vectors using PCA.

        Args:
            vectors: Vectors to compress (n_vectors, n_dimensions)

        Returns:
            Compressed vectors (n_vectors, n_components)

        """
        if self._components is None:
            # Fit PCA
            self._mean = np.mean(vectors, axis=0)
            centered = vectors - self._mean
            U, S, Vt = np.linalg.svd(centered, full_matrices=False)
            self._components = Vt[: self.n_components]

        # Transform vectors
        centered = vectors - self._mean
        return np.dot(centered, self._components.T)

    def decompress(self, compressed: NDArray) -> NDArray:
        """Decompress vectors.

        Args:
            compressed: Compressed vectors (n_vectors, n_components)

        Returns:
            Reconstructed vectors (n_vectors, n_dimensions)

        """
        if self._components is None or self._mean is None:
            raise RuntimeError("Compressor not fitted")

        reconstructed = np.dot(compressed, self._components)
        return reconstructed + self._mean


class QuantizationCompressor(VectorCompressor):
    """Vector compression using quantization."""

    def __init__(self, bits: int = 8) -> None:
        """Initialize quantization compressor.

        Args:
            bits: Number of bits per dimension

        """
        self.bits = bits
        self._min: Optional[NDArray] = None
        self._max: Optional[NDArray] = None
        self._scale: Optional[NDArray] = None

    def compress(self, vectors: NDArray) -> NDArray:
        """Compress vectors using quantization.

        Args:
            vectors: Vectors to compress (n_vectors, n_dimensions)

        Returns:
            Quantized vectors

        """
        if self._min is None:
            # Compute scaling factors
            self._min = np.min(vectors, axis=0)
            self._max = np.max(vectors, axis=0)
            self._scale = (2**self.bits - 1) / (self._max - self._min + 1e-6)

        # Quantize
        normalized = (vectors - self._min) * self._scale
        return np.round(normalized).astype(np.uint8)

    def decompress(self, compressed: NDArray) -> NDArray:
        """Decompress quantized vectors.

        Args:
            compressed: Quantized vectors

        Returns:
            Reconstructed vectors

        """
        if self._min is None or self._max is None or self._scale is None:
            raise RuntimeError("Compressor not fitted")

        return (compressed.astype(np.float32) / self._scale) + self._min


#
# Vector Pruning
#


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
