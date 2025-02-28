"""Module for vision and image processing capabilities."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

import numpy as np


@dataclass
class ImageFeatures:
    """Represents extracted features from an image."""

    features: np.ndarray
    metadata: Optional[dict] = None


@dataclass
class ImageDescription:
    """Represents a natural language description of an image."""

    text: str
    confidence: float
    metadata: Optional[dict] = None


class ImageProcessor:
    """Base class for image processing operations."""

    async def process_image(self, image_path: Union[str, Path]) -> ImageFeatures:
        """Process an image and extract features."""
        raise NotImplementedError

    async def process_batch(
        self, image_paths: List[Union[str, Path]]
    ) -> List[ImageFeatures]:
        """Process multiple images in batch."""
        raise NotImplementedError


class ImageCaptioner:
    """Base class for generating natural language descriptions of images."""

    async def generate_caption(self, image_path: Union[str, Path]) -> ImageDescription:
        """Generate a natural language description of the image."""
        raise NotImplementedError

    async def generate_captions(
        self, image_paths: List[Union[str, Path]]
    ) -> List[ImageDescription]:
        """Generate descriptions for multiple images."""
        raise NotImplementedError


class ObjectDetector:
    """Base class for detecting objects in images."""

    @dataclass
    class Detection:
        """Represents a detected object in an image."""

        label: str
        confidence: float
        bbox: tuple[
            float, float, float, float
        ]  # (x1, y1, x2, y2) normalized coordinates

    async def detect_objects(self, image_path: Union[str, Path]) -> List[Detection]:
        """Detect objects in an image."""
        raise NotImplementedError

    async def detect_batch(
        self, image_paths: List[Union[str, Path]]
    ) -> List[List[Detection]]:
        """Detect objects in multiple images."""
        raise NotImplementedError


class ImageAnalyzer:
    """High-level interface for image analysis combining multiple capabilities."""

    def __init__(
        self,
        processor: Optional[ImageProcessor] = None,
        captioner: Optional[ImageCaptioner] = None,
        detector: Optional[ObjectDetector] = None,
    ):
        self.processor = processor
        self.captioner = captioner
        self.detector = detector

    @dataclass
    class AnalysisResult:
        """Combined results from multiple analysis methods."""

        features: Optional[ImageFeatures] = None
        caption: Optional[ImageDescription] = None
        detections: Optional[List[ObjectDetector.Detection]] = None

    async def analyze(self, image_path: Union[str, Path]) -> AnalysisResult:
        """Perform comprehensive analysis of an image."""
        features = (
            await self.processor.process_image(image_path) if self.processor else None
        )
        caption = (
            await self.captioner.generate_caption(image_path)
            if self.captioner
            else None
        )
        detections = (
            await self.detector.detect_objects(image_path) if self.detector else None
        )

        return self.AnalysisResult(
            features=features, caption=caption, detections=detections
        )
