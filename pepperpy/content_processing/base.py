"""Base interfaces for content processing module."""

import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Type, Union
from pathlib import Path
from dataclasses import dataclass, field

from pepperpy.core.base import BaseProvider, ValidationError, PepperpyError
from pepperpy.core.utils import lazy_provider_class


class ContentProcessingError(PepperpyError):
    """Base error for content processing module."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Initialize a new content processing error.

        Args:
            message: Error message.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(message, *args, **kwargs)


class ContentProcessingConfigError(ContentProcessingError):
    """Error related to configuration of content processors."""

    def __init__(
        self, message: str, processor: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a new content processing configuration error.

        Args:
            message: Error message.
            processor: The processor name.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.processor = processor
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        """Return the string representation of the error."""
        if self.processor:
            return f"Configuration error for processor '{self.processor}': {self.message}"
        return f"Configuration error: {self.message}"


class ContentProcessingIOError(ContentProcessingError):
    """Error related to file I/O operations."""

    def __init__(
        self, message: str, file_path: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a new content processing I/O error.

        Args:
            message: Error message.
            file_path: The file path that caused the error.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.file_path = file_path
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        """Return the string representation of the error."""
        if self.file_path:
            return f"I/O error for file '{self.file_path}': {self.message}"
        return f"I/O error: {self.message}"


class UnsupportedContentTypeError(ContentProcessingError):
    """Error for unsupported content types."""

    def __init__(
        self, content_type: str, processor: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a new unsupported content type error.

        Args:
            content_type: The unsupported content type.
            processor: The processor name.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.content_type = content_type
        self.processor = processor
        super().__init__(
            f"Unsupported content type: {content_type}"
            + (f" for processor: {processor}" if processor else ""),
            *args,
            **kwargs,
        )


class ContentType(str, Enum):
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


class ContentProcessor(BaseProvider, ABC):
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
        self, 
        content_path: Union[str, Path], 
        **options: Any
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


def create_processor(
    content_type: str = "document",
    provider_type: Optional[str] = None,
    **config: Any
) -> ContentProcessor:
    """Create a content processor.
    
    Args:
        content_type: Type of content to process (document, image, audio, video)
        provider_type: Provider implementation to use
        **config: Additional configuration options
        
    Returns:
        Content processor instance
        
    Raises:
        ValidationError: If the content type or provider type is not supported
    """
    content_type = content_type.lower()
    
    # Determine provider type from environment if not specified
    if provider_type is None:
        env_var = f"PEPPERPY_CONTENT_PROCESSING__{content_type.upper()}__PROVIDER"
        provider_type = os.getenv(env_var)
    
    # Fallback to defaults based on content type
    if provider_type is None:
        provider_type = {
            "document": "pymupdf",
            "image": "opencv",
            "audio": "whisper",
            "video": "ffmpeg",
        }.get(content_type, "default")
    
    try:
        # Import provider module
        module_name = f"pepperpy.content_processing.providers.{content_type}.{provider_type}"
        module = importlib.import_module(module_name)

        # Get provider class
        provider_class_name = f"{provider_type.title()}ContentProcessor"
        provider_class = getattr(module, provider_class_name)

        # Create provider instance
        return provider_class(**config)
    except (ImportError, AttributeError) as e:
        raise ValidationError(f"Failed to create content processor for type '{content_type}' with provider '{provider_type}': {e}") 