"""Module for vision and image processing capabilities."""

from pathlib import Path
from typing import Any, List, Optional, Union

from .base import (
    Detection,
    ImageDescription,
    ImageFeatures,
    VisionProcessor,
)


class ImageProcessor(VisionProcessor):
    """Processor for image feature extraction."""

    async def process(
        self, image_path: Union[str, Path], **kwargs: Any
    ) -> ImageFeatures:
        """Process an image and extract features.

        Args:
            image_path: Path to the image
            **kwargs: Additional processor-specific parameters

        Returns:
            Extracted image features

        Raises:
            VisionError: If processing fails
        """
        raise NotImplementedError("process method must be implemented by subclasses")


class ImageCaptioner(VisionProcessor):
    """Processor for generating natural language descriptions of images."""

    async def process(
        self, image_path: Union[str, Path], **kwargs: Any
    ) -> ImageDescription:
        """Generate a natural language description of the image.

        Args:
            image_path: Path to the image
            **kwargs: Additional processor-specific parameters

        Returns:
            Image description

        Raises:
            VisionError: If processing fails
        """
        raise NotImplementedError("process method must be implemented by subclasses")

    async def generate_caption(self, image_path: Union[str, Path]) -> ImageDescription:
        """Generate a natural language description of the image.

        This is a convenience method that calls process().

        Args:
            image_path: Path to the image

        Returns:
            Image description

        Raises:
            VisionError: If processing fails
        """
        return await self.process(image_path)

    async def generate_captions(
        self, image_paths: List[Union[str, Path]]
    ) -> List[ImageDescription]:
        """Generate descriptions for multiple images.

        This is a convenience method that calls process_batch().

        Args:
            image_paths: List of paths to images

        Returns:
            List of image descriptions

        Raises:
            VisionError: If processing fails
        """
        return await self.process_batch(image_paths)


class ObjectDetector(VisionProcessor):
    """Processor for detecting objects in images."""

    async def process(
        self, image_path: Union[str, Path], **kwargs: Any
    ) -> List[Detection]:
        """Detect objects in an image.

        Args:
            image_path: Path to the image
            **kwargs: Additional processor-specific parameters

        Returns:
            List of detected objects

        Raises:
            VisionError: If processing fails
        """
        raise NotImplementedError("process method must be implemented by subclasses")

    async def detect_objects(self, image_path: Union[str, Path]) -> List[Detection]:
        """Detect objects in an image.

        This is a convenience method that calls process().

        Args:
            image_path: Path to the image

        Returns:
            List of detected objects

        Raises:
            VisionError: If processing fails
        """
        return await self.process(image_path)

    async def detect_batch(
        self, image_paths: List[Union[str, Path]]
    ) -> List[List[Detection]]:
        """Detect objects in multiple images.

        This is a convenience method that calls process_batch().

        Args:
            image_paths: List of paths to images

        Returns:
            List of lists of detected objects

        Raises:
            VisionError: If processing fails
        """
        return await self.process_batch(image_paths)


class ImageAnalyzer:
    """High-level interface for image analysis combining multiple capabilities."""

    def __init__(
        self,
        processor: Optional[ImageProcessor] = None,
        captioner: Optional[ImageCaptioner] = None,
        detector: Optional[ObjectDetector] = None,
    ):
        """Initialize image analyzer.

        Args:
            processor: Optional image processor for feature extraction
            captioner: Optional image captioner for generating descriptions
            detector: Optional object detector for detecting objects
        """
        self.processor = processor
        self.captioner = captioner
        self.detector = detector

    class AnalysisResult:
        """Combined results from multiple analysis methods."""

        def __init__(
            self,
            features: Optional[ImageFeatures] = None,
            caption: Optional[ImageDescription] = None,
            detections: Optional[List[Detection]] = None,
        ):
            """Initialize analysis result.

            Args:
                features: Optional extracted image features
                caption: Optional image description
                detections: Optional list of detected objects
            """
            self.features = features
            self.caption = caption
            self.detections = detections

    async def analyze(self, image_path: Union[str, Path]) -> AnalysisResult:
        """Perform comprehensive analysis of an image.

        Args:
            image_path: Path to the image

        Returns:
            Analysis result containing features, caption, and detections

        Raises:
            VisionError: If analysis fails
        """
        features = await self.processor.process(image_path) if self.processor else None
        caption = await self.captioner.process(image_path) if self.captioner else None
        detections = await self.detector.process(image_path) if self.detector else None

        return self.AnalysisResult(
            features=features, caption=caption, detections=detections
        )
