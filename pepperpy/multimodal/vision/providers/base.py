"""Base interfaces and exceptions for vision providers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class VisionError(Exception):
    """Base exception for vision errors."""

    pass


class VisionProvider(ABC):
    """Base class for vision providers."""

    @abstractmethod
    def analyze_image(
        self,
        image: Union[str, Path, bytes],
        tasks: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Analyze image using vision provider.

        Args:
            image: Path to image file, image bytes, or URL
            tasks: Optional list of analysis tasks (e.g. ['labels', 'text', 'objects'])
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict[str, Any]: Analysis results

        Raises:
            VisionError: If analysis fails
        """
        pass

    @abstractmethod
    def detect_objects(
        self,
        image: Union[str, Path, bytes],
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Detect objects in image.

        Args:
            image: Path to image file, image bytes, or URL
            **kwargs: Additional provider-specific parameters

        Returns:
            List[Dict[str, Any]]: List of detected objects with details

        Raises:
            VisionError: If detection fails
        """
        pass

    @abstractmethod
    def extract_text(
        self,
        image: Union[str, Path, bytes],
        **kwargs,
    ) -> str:
        """Extract text from image (OCR).

        Args:
            image: Path to image file, image bytes, or URL
            **kwargs: Additional provider-specific parameters

        Returns:
            str: Extracted text

        Raises:
            VisionError: If extraction fails
        """
        pass

    @abstractmethod
    def get_supported_tasks(self) -> List[str]:
        """Get list of supported analysis tasks.

        Returns:
            List[str]: List of task names
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats.

        Returns:
            List[str]: List of format extensions
        """
        pass
