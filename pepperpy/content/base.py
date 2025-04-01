"""Base interfaces for content processing module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.content.errors import (
    ContentProcessingError,
    ProviderNotFoundError,
    UnsupportedContentTypeError,
)
from pepperpy.plugins.plugin import PepperpyPlugin


class ContentType(Enum):
    """Type of content to process."""

    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass
class ProcessingResult:
    """Result of content processing."""

    # Texto extraído (para documentos, OCR em imagens, transcrição em áudio)
    text: Optional[str] = None

    # Metadados sobre o conteúdo processado
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Conteúdo extraído/processado em diferentes formatos
    extracted_text: Optional[str] = None
    extracted_images: Optional[List[Any]] = None
    audio_transcription: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None


class ContentProcessor(PepperpyPlugin, ABC):
    """Base class for content processors."""

    name: str = "base"

    def __init__(
        self,
        name: str = "base",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize content processor.

        Args:
            name: Processor name
            config: Optional configuration dictionary
            **kwargs: Additional processor-specific configuration
        """
        super().__init__(**kwargs)
        self.name = name
        self._config = config or {}
        self._config.update(kwargs)
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the processor."""
        if not self.initialized:
            self.initialized = True

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.initialized = False

    @abstractmethod
    async def process(
        self, content_path: Union[str, Path], **options: Any
    ) -> ProcessingResult:
        """Process content and return the result.

        Args:
            content_path: Path to the content file
            **options: Additional processing options

        Returns:
            Processing result with extracted content

        Raises:
            ContentProcessingError: If processing fails
        """
        raise NotImplementedError("process must be implemented by processor")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get processor capabilities.

        Returns:
            Dictionary of processor capabilities
        """
        return {
            "content_type": ContentType.DOCUMENT,
            "supports_batch": False,
            "supports_streaming": False,
            "max_file_size": None,
            "supported_formats": [],
        }


async def create_processor(
    content_type: Union[str, ContentType],
    provider_name: Optional[str] = None,
    **kwargs: Any,
) -> ContentProcessor:
    """Create content processor instance.

    Args:
        content_type: Type of content to process
        provider_name: Name of provider to use (optional)
        **kwargs: Additional configuration options

    Returns:
        Content processor instance

    Raises:
        ContentProcessingError: If processor creation fails
    """
    from pepperpy.content.lazy import (
        AVAILABLE_PROCESSORS,
        DEFAULT_PROCESSORS,
    )

    # Convert string to enum
    if isinstance(content_type, str):
        try:
            content_type = ContentType(content_type.lower())
        except ValueError:
            raise UnsupportedContentTypeError(f"Invalid content type: {content_type}")

    try:
        if provider_name:
            # Use specific provider if requested
            if content_type not in AVAILABLE_PROCESSORS:
                raise UnsupportedContentTypeError(
                    f"No providers available for content type: {content_type}"
                )

            providers = AVAILABLE_PROCESSORS[content_type]
            if provider_name not in providers:
                raise ProviderNotFoundError(
                    f"Provider not found: {provider_name} "
                    f"(available: {', '.join(providers.keys())})"
                )

            processor = providers[provider_name]
            return await processor(**kwargs)
        else:
            # Try default providers in order
            if content_type not in DEFAULT_PROCESSORS:
                raise UnsupportedContentTypeError(
                    f"No default provider for content type: {content_type}"
                )

            # Get file extension from kwargs if available
            content_path = kwargs.get("content_path")
            if content_path:
                ext = Path(content_path).suffix.lower()
                if ext == ".pdf":
                    # Try PyMuPDF first for PDF files
                    try:
                        return await AVAILABLE_PROCESSORS[content_type]["pymupdf"](
                            **kwargs
                        )
                    except Exception:
                        pass

            # Try default providers in order
            errors = []
            for processor in DEFAULT_PROCESSORS[content_type]:
                try:
                    return await processor(**kwargs)
                except Exception as e:
                    errors.append(str(e))
                    continue

            raise ContentProcessingError(
                f"No suitable provider found for content type {content_type}. "
                f"Tried: {', '.join(str(e) for e in errors)}"
            )

    except Exception as e:
        if isinstance(e, ContentProcessingError):
            raise
        raise ContentProcessingError(f"Error creating processor: {e}")
