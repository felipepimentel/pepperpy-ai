"""Image processor for synthesis.

Implements image processing for content synthesis.
"""

from typing import Any, Dict, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from ..base import SynthesisProcessor


class ImageProcessor(SynthesisProcessor):
    """Processor for image synthesis."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize image processor.

        Args:
            name: Processor name
            config: Optional configuration

        """
        super().__init__(name)
        self._config = config or {}

    async def process(self, image: NDArray) -> NDArray:
        """Process image.

        Args:
            image: Input image array (H, W, C)

        Returns:
            Processed image array

        """
        # Apply configured transformations
        result = image

        if self._config.get("resize"):
            size = self._config["resize"]
            result = self._resize(result, size)

        if self._config.get("filter"):
            result = self._apply_filter(result, self._config["filter"])

        if self._config.get("optimize", True):
            result = self._optimize(result)

        return result

    def _resize(self, image: NDArray, size: Tuple[int, int]) -> NDArray:
        """Resize image.

        Args:
            image: Input image array
            size: Target size (height, width)

        Returns:
            Resized image array

        """
        # Simple nearest neighbor resize
        h, w = size
        h_factor = h / image.shape[0]
        w_factor = w / image.shape[1]

        h_indices = np.floor(np.arange(h) / h_factor).astype(int)
        w_indices = np.floor(np.arange(w) / w_factor).astype(int)

        return image[h_indices[:, None], w_indices]

    def _apply_filter(self, image: NDArray, filter_type: str) -> NDArray:
        """Apply image filter.

        Args:
            image: Input image array
            filter_type: Type of filter to apply

        Returns:
            Filtered image array

        """
        if filter_type == "blur":
            # Apply blur filter
            kernel = np.ones((3, 3)) / 9
            result = np.zeros_like(image)
            for i in range(1, image.shape[0] - 1):
                for j in range(1, image.shape[1] - 1):
                    result[i, j] = np.sum(
                        image[i - 1 : i + 2, j - 1 : j + 2] * kernel[..., None],
                        axis=(0, 1),
                    )
            return result

        if filter_type == "sharpen":
            # Apply sharpen filter
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            result = np.zeros_like(image)
            for i in range(1, image.shape[0] - 1):
                for j in range(1, image.shape[1] - 1):
                    result[i, j] = np.sum(
                        image[i - 1 : i + 2, j - 1 : j + 2] * kernel[..., None],
                        axis=(0, 1),
                    )
            return np.clip(result, 0, 255)

        return image

    def _optimize(self, image: NDArray) -> NDArray:
        """Optimize image.

        Args:
            image: Input image array

        Returns:
            Optimized image array

        """
        # Normalize to [0, 255] range
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)

        return image
