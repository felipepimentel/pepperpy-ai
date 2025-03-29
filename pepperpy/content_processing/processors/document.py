"""Document processor implementation."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.core.base import BaseProvider
from pepperpy.content_processing.base import ContentProcessor, ContentType, ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError, UnsupportedContentTypeError


class DocumentProcessor(ContentProcessor):
    """Processor for document content."""

    def __init__(
        self,
        provider_type: str = 'pymupdf',
        **kwargs: Any,
    ) -> None:
        """Initialize document processor.

        Args:
            provider_type: Type of provider to use (pymupdf)
            **kwargs: Additional configuration options passed to the provider
        """
        super().__init__(provider_type, **kwargs)
        self._content_type = ContentType.DOCUMENT

    async def initialize(self) -> None:
        """Initialize the processor."""
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        await super().cleanup()

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process document content.

        Args:
            content_path: Path to the document file
            **options: Additional processing options
                - extract_text: bool - Extract text content
                - extract_metadata: bool - Extract document metadata
                - extract_images: bool - Extract embedded images
                - extract_tables: bool - Extract tables from document
                - extract_links: bool - Extract hyperlinks
                - extract_toc: bool - Extract table of contents
                - page_range: Tuple[int, int] - Range of pages to process
                - password: str - Password for encrypted documents
                - ocr: bool - Use OCR for text extraction
                - ocr_lang: str - Language for OCR
                - output_format: str - Format for converted document
                - compress: bool - Compress output document
                - split_pages: bool - Split document into individual pages

        Returns:
            Processing result with extracted content and metadata

        Raises:
            ContentProcessingError: If processing fails
            UnsupportedContentTypeError: If content type is not supported
        """
        # Validate content type
        if not isinstance(content_path, (str, Path)):
            raise ContentProcessingError("Content path must be a string or Path object")

        content_path = Path(content_path)
        if not content_path.exists():
            raise ContentProcessingError(f"Content path does not exist: {content_path}")

        # Process content
        try:
            result = await self._provider.process(content_path, **options)
            result.metadata['content_type'] = self._content_type.value
            return result

        except Exception as e:
            raise ContentProcessingError(f"Failed to process document: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get processor capabilities.

        Returns:
            Dictionary of processor capabilities
        """
        capabilities = {
            'content_type': self._content_type.value,
            'provider_type': self._provider_type,
        }
        capabilities.update(self._provider.get_capabilities())
        return capabilities 