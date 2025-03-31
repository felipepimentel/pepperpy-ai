"""Lazy loading module for content processing.

This module provides lazy loading functionality for content processing providers.
"""

import importlib
import logging
from typing import Any, Dict, Optional

from pepperpy.content.base import (
    ContentType,
)
from pepperpy.core.base import PepperpyError

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
        return self._instance

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
PANDOC_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content.providers.document.pandoc",
    class_name="PandocProvider",
)

TIKA_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content.providers.document.tika",
    class_name="TikaProvider",
)

TEXTRACT_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content.providers.document.textract",
    class_name="TextractProvider",
)

MAMMOTH_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content.providers.document.mammoth",
    class_name="MammothProvider",
)

PYMUPDF_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content.providers.document.pymupdf",
    class_name="PyMuPDFProvider",
)

# Image processors
TESSERACT_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content.providers.image.tesseract",
    class_name="TesseractProvider",
)

EASYOCR_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content.providers.image.easyocr",
    class_name="EasyOCRProvider",
)

# Audio processors
FFMPEG_AUDIO_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content.providers.audio.ffmpeg",
    class_name="FFmpegProvider",
)

# Video processors
FFMPEG_VIDEO_PROCESSOR = LazyContentProcessor(
    module_path="pepperpy.content.providers.video.ffmpeg",
    class_name="FFmpegProvider",
)

# Default processors by content type
DEFAULT_PROCESSORS = {
    ContentType.DOCUMENT: [
        PYMUPDF_PROCESSOR,  # Try PyMuPDF first
        TIKA_PROCESSOR,  # Then Tika
        PANDOC_PROCESSOR,  # Then Pandoc
        TEXTRACT_PROCESSOR,  # Then Textract
        MAMMOTH_PROCESSOR,  # Finally Mammoth
    ],
    ContentType.IMAGE: [
        TESSERACT_PROCESSOR,
        EASYOCR_PROCESSOR,
    ],
    ContentType.AUDIO: [
        FFMPEG_AUDIO_PROCESSOR,
    ],
    ContentType.VIDEO: [
        FFMPEG_VIDEO_PROCESSOR,
    ],
}

# All available processors by content type
AVAILABLE_PROCESSORS = {
    ContentType.DOCUMENT: {
        "pandoc": PANDOC_PROCESSOR,
        "tika": TIKA_PROCESSOR,
        "textract": TEXTRACT_PROCESSOR,
        "mammoth": MAMMOTH_PROCESSOR,
        "pymupdf": PYMUPDF_PROCESSOR,
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


async def create_processor(
    content_type: ContentType, provider_name: Optional[str] = None, **config: Any
) -> Any:
    """Create a content processor.

    Args:
        content_type: Type of content to process
        provider_name: Name of provider to use (optional)
        **config: Configuration options

    Returns:
        Content processor instance

    Raises:
        LazyLoadingError: If no suitable processor is found
    """
    if provider_name:
        # Use specific provider if requested
        if content_type not in AVAILABLE_PROCESSORS:
            raise LazyLoadingError(
                f"No providers available for content type: {content_type}"
            )

        if provider_name not in AVAILABLE_PROCESSORS[content_type]:
            raise LazyLoadingError(f"Provider not found: {provider_name}")

        processor = AVAILABLE_PROCESSORS[content_type][provider_name]
        try:
            return await processor(**config)
        except Exception as e:
            raise LazyLoadingError(f"Failed to create provider '{provider_name}': {e}")

    # Try default providers in order
    if content_type not in DEFAULT_PROCESSORS:
        raise LazyLoadingError(f"No default providers for content type: {content_type}")

    errors = []
    for processor in DEFAULT_PROCESSORS[content_type]:
        try:
            return await processor(**config)
        except Exception as e:
            errors.append(str(e))
            continue

    raise LazyLoadingError(
        f"No suitable provider found for content type {content_type}. "
        f"Tried: {', '.join(str(e) for e in errors)}"
    )
