"""DOCX document processing provider."""

from pathlib import Path
from typing import Any

from docx import Document

from pepperpy.content.base import ContentProcessor, ProcessingResult
from pepperpy.core.errors import ProviderError
from pepperpy.plugin.plugin import ProviderPlugin
from pepperpy.content.base import ContentError
from pepperpy.content import ContentProvider
from pepperpy.content.base import ContentError


class DocxProvider(class DocxProvider(ContentProvider, ProviderPlugin):
    """DOCX document processing provider."""):
    """
    Content docx provider.
    
    This provider implements docx functionality for the PepperPy content framework.
    """

    def __init__(self, **kwargs: Any) -> None:


    """Initialize provider.



    Args:


        **kwargs: Parameter description


    """
        super().__init__(**kwargs)
        self._initialized = False

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
 """
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
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
 """
        self._initialized = False
