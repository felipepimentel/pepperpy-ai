"""DOCX document processing provider."""

from pathlib import Path
from typing import Any

from docx import Document

from pepperpy.content.base import ContentProcessor, ProcessingResult
from pepperpy.core.errors import ProviderError
from pepperpy.plugins.plugin import ProviderPlugin


class DocxProvider(ContentProcessor, ProviderPlugin):
    """DOCX document processing provider."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize provider."""
        super().__init__(**kwargs)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize provider."""
        if self._initialized:
            return

        self._initialized = True

    async def process(self, content: Path | str, **kwargs: Any) -> ProcessingResult:
        """Process document.

        Args:
            content: Path to document
            **kwargs: Additional arguments

        Returns:
            Processing result with extracted text and metadata

        Raises:
            ProviderError: If processing fails
        """
        try:
            # Convert content to Path
            if isinstance(content, str):
                content = Path(content)

            # Check if file exists
            if not content.exists():
                raise ProviderError(f"File not found: {content}")

            # Open document
            doc = Document(str(content))

            # Extract text from paragraphs
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])

            # Basic metadata
            metadata = {
                "title": doc.core_properties.title or "",
                "author": doc.core_properties.author or "",
                "created": str(doc.core_properties.created)
                if doc.core_properties.created
                else "",
                "modified": str(doc.core_properties.modified)
                if doc.core_properties.modified
                else "",
            }

            return ProcessingResult(text=text, metadata=metadata)

        except Exception as e:
            raise ProviderError(f"Failed to process document: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False
