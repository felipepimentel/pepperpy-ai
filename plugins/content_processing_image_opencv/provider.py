"""OpenCV provider for image processing."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from pepperpy.core.utils import lazy_provider_class
from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError

try:
    import cv2
except ImportError:
    cv2 = None


@lazy_provider_class("content_processing.image", "opencv")
class OpenCVProvider:
    """Provider for image processing using OpenCV."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize OpenCV provider.

        Args:
            **kwargs: Additional configuration options
        """
        self._config = kwargs
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            if cv2 is None:
                raise ContentProcessingError(
                    "OpenCV is not installed. Install with: pip install opencv-python"
                )
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process image using OpenCV.

        Args:
            content_path: Path to the image file
            **options: Additional processing options
                - resize: Tuple[int, int] - Target size for resizing
                - grayscale: bool - Convert to grayscale
                - blur: Tuple[int, int] - Gaussian blur kernel size
                - edge_detection: bool - Apply Canny edge detection
                - face_detection: bool - Detect faces in image
                - object_detection: bool - Detect objects in image
                - save_processed: bool - Save processed image

        Returns:
            Processing result with extracted content and detections

        Raises:
            ContentProcessingError: If processing fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Read image
            img = cv2.imread(str(content_path))
            if img is None:
                raise ContentProcessingError(f"Failed to read image: {content_path}")

            # Get original metadata
            metadata = {
                'dimensions': img.shape[:2],  # height, width
                'height': img.shape[0],
                'width': img.shape[1],
                'channels': img.shape[2] if len(img.shape) > 2 else 1,
                'dtype': str(img.dtype),
            }

            # Convert to grayscale if requested
            if options.get('grayscale'):
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                metadata['processed'] = {'grayscale': True}

            # Resize if requested
            if 'resize' in options:
                width, height = options['resize']
                img = cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)
                metadata['processed'] = metadata.get('processed', {})
                metadata['processed']['resize'] = {'width': width, 'height': height}

            # Apply Gaussian blur if requested
            if 'blur' in options:
                ksize_x, ksize_y = options['blur']
                img = cv2.GaussianBlur(img, (ksize_x, ksize_y), 0)
                metadata['processed'] = metadata.get('processed', {})
                metadata['processed']['blur'] = {'kernel_size': (ksize_x, ksize_y)}

            # Apply edge detection if requested
            if options.get('edge_detection'):
                if len(img.shape) > 2:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    gray = img
                edges = cv2.Canny(gray, 100, 200)
                metadata['processed'] = metadata.get('processed', {})
                metadata['processed']['edge_detection'] = True
                if options.get('save_processed'):
                    img = edges

            # Detect faces if requested
            if options.get('face_detection'):
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                if len(img.shape) > 2:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    gray = img
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                metadata['detections'] = metadata.get('detections', {})
                metadata['detections']['faces'] = [
                    {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)}
                    for (x, y, w, h) in faces
                ]

            # Save processed image if requested
            if options.get('save_processed'):
                output_path = Path(str(content_path)).with_stem(f"{Path(content_path).stem}_processed")
                cv2.imwrite(str(output_path), img)
                metadata['processed_path'] = str(output_path)

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process image with OpenCV: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            'supports_metadata': True,
            'supports_resize': True,
            'supports_grayscale': True,
            'supports_blur': True,
            'supports_edge_detection': True,
            'supports_face_detection': True,
            'supported_formats': [
                '.jpg',
                '.jpeg',
                '.png',
                '.bmp',
                '.tiff',
            ],
        } 