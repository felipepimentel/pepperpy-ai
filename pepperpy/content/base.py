"""Base interfaces for content processing module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pepperpy.core.base import PepperpyError
from pepperpy.plugin import PepperpyPlugin


class ContentProcessingError(PepperpyError):
    """Base error for content processing."""

    pass


class ContentProcessingConfigError(ContentProcessingError):
    """Error raised when there is a configuration issue."""

    pass


class ContentProcessingIOError(ContentProcessingError):
    """Error raised when there is an I/O issue."""

    pass


class UnsupportedContentTypeError(ContentProcessingError):
    """Error raised when content type is not supported."""

    pass


class ProviderNotFoundError(ContentProcessingError):
    """Error raised when provider is not found."""

    pass


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
    text: str | None = None

    # Metadados sobre o conteúdo processado
    metadata: dict[str, Any] = field(default_factory=dict)

    # Conteúdo extraído/processado em diferentes formatos
    extracted_text: str | None = None
    extracted_images: list[Any] | None = None
    audio_transcription: str | None = None
    structured_data: dict[str, Any] | None = None


class ContentProcessor(PepperpyPlugin, ABC):
    """Base class for content processors."""

    name: str = "base"

    def __init__(
        self,
        name: str = "base",
        config: dict[str, Any] | None = None,
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
        self, content_path: str | Path, **options: Any
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

    def get_capabilities(self) -> dict[str, Any]:
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
    content_type: str | ContentType,
    provider_name: str | None = None,
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


class Entity:
    """Representation of an extracted entity."""

    def __init__(
        self,
        text: str,
        label: str,
        start_char: int,
        end_char: int,
        score: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.text = text
        self.label = label
        self.start_char = start_char
        self.end_char = end_char
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert entity to dictionary."""
        result = {
            "text": self.text,
            "label": self.label,
            "start": self.start_char,
            "end": self.end_char,
        }
        if self.score is not None:
            result["score"] = self.score
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class Relationship:
    """Representation of a relationship between entities."""

    def __init__(
        self,
        source: Entity,
        target: Entity,
        relation_type: str,
        score: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.source = source
        self.target = target
        self.relation_type = relation_type
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert relationship to dictionary."""
        result = {
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "relation": self.relation_type,
        }
        if self.score is not None:
            result["score"] = self.score
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class SemanticExtractionResult:
    """Result of semantic extraction."""

    def __init__(
        self,
        text: str,
        entities: list[Entity] | None = None,
        relationships: list[Relationship] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.text = text
        self.entities = entities or []
        self.relationships = relationships or []
        self.metadata = metadata or {}

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the result."""
        self.entities.append(entity)

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the result."""
        self.relationships.append(relationship)

    def get_entities_by_label(self, label: str) -> list[Entity]:
        """Get entities by label."""
        return [e for e in self.entities if e.label == label]

    def get_relationships_by_type(self, relation_type: str) -> list[Relationship]:
        """Get relationships by type."""
        return [r for r in self.relationships if r.relation_type == relation_type]

    def to_dict(self) -> dict[str, Any]:
        """Convert extraction result to dictionary."""
        return {
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "metadata": self.metadata,
        }


class SemanticProcessor(Protocol):
    """Protocol for semantic processors."""

    async def process_text(self, text: str, **kwargs: Any) -> SemanticExtractionResult:
        """Process text to extract semantic information.

        Args:
            text: Text to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Semantic extraction result
        """
        ...

    async def extract_entities(self, text: str, **kwargs: Any) -> list[Entity]:
        """Extract entities from text.

        Args:
            text: Text to process
            **kwargs: Additional processor-specific parameters

        Returns:
            List of extracted entities
        """
        ...

    async def extract_relationships(
        self, text: str, **kwargs: Any
    ) -> list[Relationship]:
        """Extract relationships from text.

        Args:
            text: Text to process
            **kwargs: Additional processor-specific parameters

        Returns:
            List of extracted relationships
        """
        ...


class SemanticProcessorProvider(ABC):
    """Base class for semantic processor providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the processor."""
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    @abstractmethod
    async def process_text(self, text: str, **kwargs: Any) -> SemanticExtractionResult:
        """Process text to extract semantic information."""
        ...

    @abstractmethod
    async def extract_entities(self, text: str, **kwargs: Any) -> list[Entity]:
        """Extract entities from text."""
        ...

    @abstractmethod
    async def extract_relationships(
        self, text: str, **kwargs: Any
    ) -> list[Relationship]:
        """Extract relationships from text."""
        ...


def create_semantic_processor(
    provider_type: str = "default", **config: Any
) -> SemanticProcessor:
    """Create a semantic processor instance.

    Args:
        provider_type: Type of processor to create
        **config: Processor configuration

    Returns:
        Semantic processor instance
    """
    from pepperpy.plugin import create_provider_instance

    return create_provider_instance("content", f"semantic.{provider_type}", **config)


class ContentError(PepperpyError):
    """Base error for content processing operations."""

    pass


class TextNormalizationError(ContentError):
    """Error raised during text normalization operations."""

    pass


@runtime_checkable
class TextNormalizer(Protocol):
    """Protocol for text normalizers.

    This protocol defines the interface that all text normalizers must implement.
    """

    def normalize(self, text: str) -> str:
        """Apply all configured normalizations to text.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        ...

    async def initialize(self) -> None:
        """Initialize the normalizer with required resources."""
        ...

    async def cleanup(self) -> None:
        """Clean up any resources used by the normalizer."""
        ...


class BaseContentProvider(ABC):
    """Base class for content providers.

    This class provides common functionality for all content providers,
    including configuration management and resource handling.
    """

    def __init__(
        self, name: str = "base", config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize the provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.initialized = False

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider resources."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        pass
