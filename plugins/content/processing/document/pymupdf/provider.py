"""PyMuPDF document processing provider."""

from pathlib import Path
from typing import Any

import fitz

from pepperpy.content.base import ContentProcessor, ProcessingResult
from pepperpy.core.errors import ProviderError
from pepperpy.plugin.plugin import ProviderPlugin
from pepperpy.content.base import ContentError
from pepperpy.content import ContentProvider
from pepperpy.content.base import ContentError


class PyMuPDFProvider(class PyMuPDFProvider(ContentProvider, ProviderPlugin):
    """PyMuPDF document processing provider."""):
    """
    Content pymupdf provider.
    
    This provider implements pymupdf functionality for the PepperPy content framework.
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
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
 """
        self._initialized = False
