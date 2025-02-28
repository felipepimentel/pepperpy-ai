"""Vision processing capabilities for the PepperPy framework.

This module provides functionality for processing and analyzing images:
- Image processing: Extract features from images
- Image captioning: Generate natural language descriptions of images
- Object detection: Identify and locate objects within images
- Vision providers: Integration with external vision APIs
"""

from .processing import (
    ImageAnalyzer,
    ImageCaptioner,
    ImageDescription,
    ImageFeatures,
    ImageProcessor,
    ObjectDetector,
)

__all__ = [
    # Core classes
    "ImageProcessor",
    "ImageCaptioner",
    "ObjectDetector",
    "ImageAnalyzer",
    
    # Data classes
    "ImageFeatures",
    "ImageDescription",
] 