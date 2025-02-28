"""Vector compression for memory optimization.

Implements vector compression techniques to reduce memory usage
while maintaining search quality.
"""

from typing import Optional

import numpy as np
from numpy.typing import NDArray


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
