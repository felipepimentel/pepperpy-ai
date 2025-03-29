"""Lazy loading module for content processing.

This module provides lazy loading functionality for content processing providers.
"""

import importlib
import logging
from typing import Any, Dict, Optional, Type

from pepperpy.core.base import PepperpyError
from pepperpy.content_processing.base import ContentProcessor, ContentType
from pepperpy.content_processing.errors import ContentProcessingError

logger = logging.getLogger(__name__)


class LazyLoadingError(PepperpyError):
    """Error raised during lazy loading."""

    pass


class LazyContentProcessor:
    """Lazy loading wrapper for content processors."""

    def __init__(
        self,
        module_path: str,
        class_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize lazy content processor.

        Args:
            module_path: Path to module containing processor class
            class_name: Name of processor class
            config: Configuration options (optional)
        """
        self._module_path = module_path
        self._class_name = class_name
        self._config = config or {}
        self._instance = None

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call processor instance.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Processing result

        Raises:
            LazyLoadingError: If loading fails
        """
        if self._instance is None:
            self._instance = await self._load_instance()
        return await self._instance(*args, **kwargs)

    async def _load_instance(self) -> Any:
        """Load processor instance.

        Returns:
            Processor instance

        Raises:
            LazyLoadingError: If loading fails
        """
        try:
            # Import module
            module = importlib.import_module(self._module_path)

            # Get class
            cls = getattr(module, self._class_name)

            # Create instance
            instance = cls(**self._config)

            # Initialize if needed
            if hasattr(instance, "initialize"):
                await instance.initialize()

            return instance

        except Exception as e:
            raise LazyLoadingError(f"Error loading processor: {e}")


# Document processors
PYMUPDF_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content_processing.providers.document.pymupdf",
    class_name="PyMuPDFProvider",
)

PANDOC_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content_processing.providers.document.pandoc",
    class_name="PandocProvider",
)

TIKA_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content_processing.providers.document.tika",
    class_name="TikaProvider",
)

TEXTRACT_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content_processing.providers.document.textract",
    class_name="TextractProvider",
)

MAMMOTH_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content_processing.providers.document.mammoth",
    class_name="MammothProvider",
)

# Image processors
TESSERACT_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content_processing.providers.image.tesseract",
    class_name="TesseractProvider",
)

EASYOCR_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content_processing.providers.image.easyocr",
    class_name="EasyOCRProvider",
)

# Audio processors
FFMPEG_AUDIO_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content_processing.providers.audio.ffmpeg",
    class_name="FFmpegProvider",
)

# Video processors
FFMPEG_VIDEO_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content_processing.providers.video.ffmpeg",
    class_name="FFmpegProvider",
)

# Default processors by content type
DEFAULT_PROCESSORS = {
    ContentType.DOCUMENT: PYMUPDF_PROCESSOR,
    ContentType.IMAGE: TESSERACT_PROCESSOR,
    ContentType.AUDIO: FFMPEG_AUDIO_PROCESSOR,
    ContentType.VIDEO: FFMPEG_VIDEO_PROCESSOR,
}

# All available processors by content type
AVAILABLE_PROCESSORS = {
    ContentType.DOCUMENT: {
        "pymupdf": PYMUPDF_PROCESSOR,
        "pandoc": PANDOC_PROCESSOR,
        "tika": TIKA_PROCESSOR,
        "textract": TEXTRACT_PROCESSOR,
        "mammoth": MAMMOTH_PROCESSOR,
    },
    ContentType.IMAGE: {
        "tesseract": TESSERACT_PROCESSOR,
        "easyocr": EASYOCR_PROCESSOR,
    },
    ContentType.AUDIO: {
        "ffmpeg": FFMPEG_AUDIO_PROCESSOR,
    },
    ContentType.VIDEO: {
        "ffmpeg": FFMPEG_VIDEO_PROCESSOR,
    },
} 