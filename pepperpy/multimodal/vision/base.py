"""Base classes and interfaces for the vision processing system.

This module provides the core abstractions for the vision processing system:
- ImageFeatures: Container for extracted features from images
- ImageDescription: Representation of image descriptions
- VisionProcessor: Base class for all vision processors
- VisionProvider: Base class for vision service providers
"""

from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Try to import numpy, but provide fallbacks if not available
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

from ..base import (
    ContentType,
    DataFormat,
    MultimodalError,
    MultimodalProcessor,
    MultimodalProvider,
)


class VisionError(MultimodalError):
    """Base exception for vision-related errors."""

    def __init__(
        self,
        message: str,
        *,
        component: Optional[str] = None,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            component: Optional component name that caused the error
            provider: Optional provider name that caused the error
            details: Optional additional details
        """
        super().__init__(
            message, component=component, provider=provider, details=details
        )


@dataclass
class ImageFeatures:
    """Represents extracted features from an image."""

    features: Any  # np.ndarray when numpy is available
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ImageDescription:
    """Represents a natural language description of an image."""

    text: str
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BoundingBox:
    """Represents a bounding box in an image."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        """Get the width of the bounding box.

        Returns:
            Width of the bounding box
        """
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Get the height of the bounding box.

        Returns:
            Height of the bounding box
        """
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        """Get the area of the bounding box.

        Returns:
            Area of the bounding box
        """
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        """Get the center coordinates of the bounding box.

        Returns:
            Center coordinates (x, y)
        """
        return (self.x1 + self.width / 2, self.y1 + self.height / 2)

    @classmethod
    def from_tuple(cls, bbox: Tuple[float, float, float, float]) -> "BoundingBox":
        """Create a BoundingBox from a tuple of coordinates.

        Args:
            bbox: Tuple of (x1, y1, x2, y2) coordinates

        Returns:
            BoundingBox instance
        """
        return cls(x1=bbox[0], y1=bbox[1], x2=bbox[2], y2=bbox[3])

    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Convert to a tuple of coordinates.

        Returns:
            Tuple of (x1, y1, x2, y2) coordinates
        """
        return (self.x1, self.y1, self.x2, self.y2)


@dataclass
class Detection:
    """Represents a detected object in an image."""

    label: str
    confidence: float
    bbox: BoundingBox
    metadata: Optional[Dict[str, Any]] = None


class VisionProcessor(MultimodalProcessor):
    """Base class for all vision processors."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        supported_formats: Optional[List[DataFormat]] = None,
    ) -> None:
        """Initialize vision processor.

        Args:
            name: Processor name
            config: Optional configuration
            supported_formats: List of supported image formats
        """
        if supported_formats is None:
            supported_formats = [
                DataFormat.JPEG,
                DataFormat.PNG,
                DataFormat.GIF,
                DataFormat.WEBP,
            ]

        super().__init__(
            name,
            config=config,
            supported_content_types=[ContentType.IMAGE],
            supported_formats=supported_formats,
        )

    @abstractmethod
    async def process(self, image_path: Union[str, Path], **kwargs: Any) -> Any:
        """Process an image.

        Args:
            image_path: Path to the image
            **kwargs: Additional processor-specific parameters

        Returns:
            Processed image data

        Raises:
            VisionError: If processing fails
        """
        pass

    async def process_batch(
        self, image_paths: List[Union[str, Path]], **kwargs: Any
    ) -> List[Any]:
        """Process multiple images in batch.

        Args:
            image_paths: List of paths to images
            **kwargs: Additional processor-specific parameters

        Returns:
            List of processed image data

        Raises:
            VisionError: If processing fails
        """
        results = []
        for path in image_paths:
            results.append(await self.process(path, **kwargs))
        return results


class VisionProvider(MultimodalProvider):
    """Base class for vision service providers."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        supported_formats: Optional[List[DataFormat]] = None,
    ) -> None:
        """Initialize vision provider.

        Args:
            name: Provider name
            config: Optional configuration
            supported_formats: List of supported image formats
        """
        if supported_formats is None:
            supported_formats = [
                DataFormat.JPEG,
                DataFormat.PNG,
                DataFormat.GIF,
                DataFormat.WEBP,
            ]

        super().__init__(
            name,
            config=config,
            supported_content_types=[ContentType.IMAGE],
            supported_formats=supported_formats,
        )

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        Raises:
            VisionError: If initialization fails
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider.

        Raises:
            VisionError: If shutdown fails
        """
        pass

    async def save_image(
        self, image: Any, path: Union[str, Path], format: Optional[DataFormat] = None
    ) -> Path:
        """Save image data to file.

        Args:
            image: Image data to save
            path: Output file path
            format: Optional output format

        Returns:
            Path to saved file

        Raises:
            VisionError: If saving fails
        """
        raise NotImplementedError("save_image method must be implemented by subclasses")
