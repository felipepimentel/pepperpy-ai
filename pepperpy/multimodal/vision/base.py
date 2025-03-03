"""Base classes and interfaces for the vision processing system.

This module provides the core abstractions for vision processing in PepperPy.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Union

from pepperpy.formats.image import ImageData


@dataclass
class BoundingBox:
    """Bounding box for object detection."""

    x: float
    y: float
    width: float
    height: float
    confidence: float = 1.0


@dataclass
class Detection:
    """Object detection result."""

    label: str
    confidence: float
    bounding_box: BoundingBox


@dataclass
class ImageFeatures:
    """Features extracted from an image."""

    features: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageDescription:
    """Natural language description of an image."""

    text: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class VisionError(Exception):
    """Base exception for vision processing errors."""



class VisionProcessor(ABC):
    """Base class for vision processors."""

    @abstractmethod
    async def process(
        self, image_path: Union[str, Path], **kwargs: Any,
    ) -> Union[ImageFeatures, ImageDescription, List[Detection], ImageData]:
        """Process an image.

        Args:
            image_path: Path to the image
            **kwargs: Additional processor-specific parameters

        Returns:
            Processing result

        Raises:
            VisionError: If processing fails

        """


class ImageLoader:
    """Utility for loading and preprocessing images."""

    @staticmethod
    def load(image_path: Union[str, Path]) -> ImageData:
        """Load an image from file.

        Args:
            image_path: Path to the image

        Returns:
            Loaded image data

        Raises:
            VisionError: If image loading fails

        """
        try:
            import numpy as np
            from PIL import Image

            image_path = Path(image_path)
            img = Image.open(image_path)

            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Convert to numpy array
            data = np.array(img)

            return ImageData(
                data=data,
                width=img.width,
                height=img.height,
                channels=3,
                mode="RGB",
                metadata={"path": str(image_path)},
            )
        except ImportError:
            raise VisionError("PIL and numpy are required for image loading") from None
        except Exception as e:
            raise VisionError(f"Failed to load image: {e!s}") from e

    @staticmethod
    def resize(image: ImageData, width: int, height: int) -> ImageData:
        """Resize an image.

        Args:
            image: Image data
            width: Target width
            height: Target height

        Returns:
            Resized image data

        Raises:
            VisionError: If resizing fails

        """
        try:
            import numpy as np
            from PIL import Image

            # Convert to PIL Image
            pil_image = Image.fromarray(image.data)

            # Resize
            resized = pil_image.resize((width, height))

            # Convert back to numpy array
            data = np.array(resized)

            return ImageData(
                data=data,
                width=width,
                height=height,
                channels=image.channels,
                mode=image.mode,
                metadata=image.metadata,
            )
        except ImportError:
            raise VisionError("PIL and numpy are required for image resizing") from None
        except Exception as e:
            raise VisionError(f"Failed to resize image: {e!s}") from e

    @staticmethod
    def normalize(image: ImageData) -> ImageData:
        """Normalize image pixel values to [0, 1].

        Args:
            image: Image data

        Returns:
            Normalized image data

        Raises:
            VisionError: If normalization fails

        """
        try:
            import numpy as np

            # Normalize to [0, 1]
            normalized_data = image.data.astype(np.float32) / 255.0

            return ImageData(
                data=normalized_data,
                width=image.width,
                height=image.height,
                channels=image.channels,
                mode=image.mode,
                metadata=image.metadata,
            )
        except ImportError:
            raise VisionError("Numpy is required for image normalization") from None
        except Exception as e:
            raise VisionError(f"Failed to normalize image: {e!s}") from e

    @staticmethod
    def to_tensor(image: ImageData) -> Any:
        """Convert image to tensor format for ML models.

        Args:
            image: Image data

        Returns:
            Tensor representation of the image

        Raises:
            VisionError: If conversion fails

        """
        try:
            import numpy as np

            # Ensure image is normalized
            if image.data.dtype != np.float32:
                image = ImageLoader.normalize(image)

            # Transpose to channel-first format (C, H, W) for PyTorch
            tensor_data = np.transpose(image.data, (2, 0, 1))

            return tensor_data
        except ImportError:
            raise VisionError("Numpy is required for tensor conversion") from None
        except Exception as e:
            raise VisionError(f"Failed to convert image to tensor: {e!s}") from e


# Re-export ImageData for convenience
__all__ = [
    "BoundingBox",
    "Detection",
    "ImageData",
    "ImageDescription",
    "ImageFeatures",
    "ImageLoader",
    "VisionError",
    "VisionProcessor",
]
