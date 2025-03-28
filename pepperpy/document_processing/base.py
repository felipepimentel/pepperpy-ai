"""Base interfaces and factory functions for document processing.

This module provides the base interfaces, types, and factory functions for
document processing providers, supporting different document processing libraries.

Example:
    >>> from pepperpy.document_processing import create_provider
    >>> provider = create_provider("pymupdf")
    >>> text = await provider.extract_text("document.pdf")
"""

import os
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from pepperpy.core.base import BaseProvider, PepperpyError


class DocumentProcessingError(PepperpyError):
    """Error raised during document processing."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        document_path: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a document processing error.

        Args:
            message: Error message
            provider: Optional provider name
            document_path: Optional document path
            **kwargs: Additional error context
        """
        super().__init__(message, **kwargs)
        self.provider = provider
        self.document_path = document_path

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            Error message with provider and document path if available
        """
        parts = [self.message]
        if self.provider:
            parts.append(f"Provider: {self.provider}")
        if self.document_path:
            parts.append(f"Document: {self.document_path}")
        return " | ".join(parts)


@dataclass
class DocumentMetadata:
    """Metadata for a document.

    Attributes:
        filename: Original filename
        content_type: MIME type of the document
        creation_date: Creation date of the document
        modification_date: Last modification date
        author: Document author
        title: Document title
        page_count: Number of pages (for multi-page documents)
        word_count: Number of words
        language: Document language
        custom: Custom metadata
    """

    filename: str
    content_type: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentContent:
    """Content extracted from a document.

    Attributes:
        text: Plain text content
        metadata: Document metadata
        pages: Page contents for multi-page documents
        images: Extracted images
        tables: Extracted tables
    """

    text: str
    metadata: DocumentMetadata
    pages: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[Dict[str, Any]]] = None
    tables: Optional[List[Dict[str, Any]]] = None


class DocumentType(Enum):
    """Types of documents that can be processed."""

    PDF = auto()
    TEXT = auto()
    MARKDOWN = auto()
    HTML = auto()
    DOCX = auto()
    CSV = auto()
    IMAGE = auto()
    UNKNOWN = auto()

    @classmethod
    def from_extension(cls, extension: str) -> "DocumentType":
        """Get document type from file extension.

        Args:
            extension: File extension (with or without dot)

        Returns:
            Document type
        """
        if extension.startswith("."):
            extension = extension[1:]

        extension = extension.lower()

        if extension == "pdf":
            return cls.PDF
        elif extension in ["txt", "text"]:
            return cls.TEXT
        elif extension in ["md", "markdown"]:
            return cls.MARKDOWN
        elif extension in ["html", "htm"]:
            return cls.HTML
        elif extension in ["docx", "doc"]:
            return cls.DOCX
        elif extension == "csv":
            return cls.CSV
        elif extension in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]:
            return cls.IMAGE
        else:
            return cls.UNKNOWN


class DocumentProcessingProvider(BaseProvider):
    """Base class for document processing providers."""

    def __init__(
        self,
        name: str = "base",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize document processing provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(name=name, config=config, **kwargs)

    @abstractmethod
    async def extract_text(
        self,
        file_path: Union[str, Path],
        **kwargs: Any,
    ) -> str:
        """Extract text from a document.

        Args:
            file_path: Path to document
            **kwargs: Additional provider-specific arguments

        Returns:
            Extracted text

        Raises:
            DocumentProcessingError: If text extraction fails
        """
        pass

    @abstractmethod
    async def extract_metadata(
        self,
        file_path: Union[str, Path],
        **kwargs: Any,
    ) -> DocumentMetadata:
        """Extract metadata from a document.

        Args:
            file_path: Path to document
            **kwargs: Additional provider-specific arguments

        Returns:
            Document metadata

        Raises:
            DocumentProcessingError: If metadata extraction fails
        """
        pass

    async def process_document(
        self,
        file_path: Union[str, Path],
        extract_images: bool = False,
        extract_tables: bool = False,
        **kwargs: Any,
    ) -> DocumentContent:
        """Process a document, extracting text, metadata, and optional elements.

        Args:
            file_path: Path to document
            extract_images: Whether to extract images
            extract_tables: Whether to extract tables
            **kwargs: Additional provider-specific arguments

        Returns:
            Processed document content

        Raises:
            DocumentProcessingError: If document processing fails
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            # Extract text and metadata
            text = await self.extract_text(file_path, **kwargs)
            metadata = await self.extract_metadata(file_path, **kwargs)

            # Create document content
            content = DocumentContent(
                text=text,
                metadata=metadata,
            )

            # Extract images if requested
            if extract_images and hasattr(self, "extract_images"):
                try:
                    # Using type ignore to bypass the linter error
                    # We're using hasattr to check if the method exists at runtime
                    # pylint: disable=no-member
                    extract_images_method = self.extract_images  # type: ignore
                    content.images = await extract_images_method(file_path, **kwargs)
                except Exception:
                    # Don't fail the whole process if image extraction fails
                    pass

            # Extract tables if requested
            if extract_tables and hasattr(self, "extract_tables"):
                try:
                    # Using type ignore to bypass the linter error
                    # We're using hasattr to check if the method exists at runtime
                    # pylint: disable=no-member
                    extract_tables_method = self.extract_tables  # type: ignore
                    content.tables = await extract_tables_method(file_path, **kwargs)
                except Exception:
                    # Don't fail the whole process if table extraction fails
                    pass

            return content

        except Exception as e:
            raise DocumentProcessingError(
                f"Document processing failed: {e}",
                provider=self.name,
                document_path=str(file_path),
            )

    def supports_document_type(self, document_type: DocumentType) -> bool:
        """Check if this provider supports the given document type.

        Args:
            document_type: Document type to check

        Returns:
            True if supported, False otherwise
        """
        # Default implementation, providers should override
        return document_type in self.get_supported_document_types()

    def get_supported_document_types(self) -> List[DocumentType]:
        """Get list of document types supported by this provider.

        Returns:
            List of supported document types
        """
        # Default implementation, providers should override
        return [DocumentType.TEXT]


# Provider registry
_PROVIDERS: Dict[str, Type[DocumentProcessingProvider]] = {}


def register_provider(
    name: str, provider_class: Type[DocumentProcessingProvider]
) -> None:
    """Register a document processing provider.

    Args:
        name: Provider name
        provider_class: Provider class
    """
    _PROVIDERS[name.lower()] = provider_class


def create_provider(
    provider_type: Optional[str] = None,
    **config: Any,
) -> DocumentProcessingProvider:
    """Create a document processing provider.

    Args:
        provider_type: Provider type, defaults to environment variable
        **config: Provider configuration

    Returns:
        Document processing provider

    Raises:
        ValueError: If provider type is not found
    """
    # Get provider type from environment variable if not specified
    if provider_type is None:
        provider_type = os.environ.get(
            "PEPPERPY_DOCUMENT_PROCESSING__PROVIDER", "default"
        )

    # Ensure provider_type is not None at this point
    provider_name = "default" if provider_type is None else provider_type.lower()

    # Import and register built-in providers
    _register_builtin_providers()

    # Fallback to default if specified provider is not found
    if provider_name not in _PROVIDERS and provider_name != "default":
        raise ValueError(f"Document processing provider not found: {provider_name}")

    # Use default provider if specified or if provider_type is "default"
    if provider_name == "default" or provider_name not in _PROVIDERS:
        # Try to find the first available provider in order of preference
        for preferred in ["pymupdf", "langchain", "nltk", "docling"]:
            if preferred in _PROVIDERS:
                provider_name = preferred
                break
        else:
            # Fallback to first registered provider or raise error
            if _PROVIDERS:
                provider_name = next(iter(_PROVIDERS.keys()))
            else:
                raise ValueError("No document processing providers found")

    return _PROVIDERS[provider_name](**config)


def _register_builtin_providers() -> None:
    """Register built-in providers."""
    # Import and register PyMuPDF provider if available
    try:
        from .providers.pymupdf_provider import PyMuPDFProvider

        register_provider("pymupdf", PyMuPDFProvider)
    except (ImportError, ModuleNotFoundError):
        pass

    # Import and register LangChain provider if available
    try:
        from .providers.langchain_provider import LangChainProvider

        register_provider("langchain", LangChainProvider)
    except (ImportError, ModuleNotFoundError):
        pass

    # Import and register Docling provider if available
    try:
        from .providers.docling_provider import DoclingProvider

        register_provider("docling", DoclingProvider)
    except (ImportError, ModuleNotFoundError):
        pass

    # Import and register LlamaParse provider if available
    try:
        from .providers.llamaparse_provider import LlamaParseProvider

        register_provider("llamaparse", LlamaParseProvider)
    except (ImportError, ModuleNotFoundError):
        pass
