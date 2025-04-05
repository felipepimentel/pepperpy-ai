"""PyMuPDF document processing provider."""

from pathlib import Path
from typing import Any

import fitz

from pepperpy.content.base import ContentProcessor, ProcessingResult
from pepperpy.core.errors import ProviderError
from pepperpy.plugin.plugin import ProviderPlugin


class PyMuPDFProvider(ContentProcessor, ProviderPlugin):
    """PyMuPDF document processing provider."""

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
            doc = fitz.open(str(content))

            # Extract text
            text = ""
            for page in doc:
                text += page.get_text()

            # Extract metadata
            metadata = doc.metadata

            # Close document
            doc.close()

            return ProcessingResult(text=text, metadata=metadata)

        except Exception as e:
            raise ProviderError(f"Failed to process document: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False
