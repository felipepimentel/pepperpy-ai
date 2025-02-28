"""Vision processing capabilities for the PepperPy framework.

This module provides functionality for processing and analyzing images:
- Image feature extraction
- Object detection
- Image captioning and description
- Image analysis
"""

from .base import (
    BoundingBox,
    Detection,
    ImageDescription,
    ImageFeatures,
    VisionError,
    VisionProcessor,
    VisionProvider,
)
from .processing import (
    ImageAnalyzer,
    ImageCaptioner,
    ImageProcessor,
    ObjectDetector,
)

__all__ = [
    # Base classes
    "BoundingBox",
    "Detection",
    "ImageDescription",
    "ImageFeatures",
    "VisionError",
    "VisionProcessor",
    "VisionProvider",
    # Processing classes
    "ImageAnalyzer",
    "ImageCaptioner",
    "ImageProcessor",
    "ObjectDetector",
]
