"""Text file processing provider."""

from pathlib import Path
from typing import Any

from pepperpy.content.base import ContentProcessor, ProcessingResult
from pepperpy.core.errors import ProviderError
from pepperpy.plugins.plugin import ProviderPlugin


class TextProvider(ContentProcessor, ProviderPlugin):
    """Text file processing provider."""

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
        """Process text file.

        Args:
            content: Path to text file
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

            # Read text file
            text = content.read_text()

            # Basic metadata
            metadata = {
                "filename": content.name,
                "size": content.stat().st_size,
                "modified": content.stat().st_mtime,
            }

            return ProcessingResult(text=text, metadata=metadata)

        except Exception as e:
            raise ProviderError(f"Failed to process text file: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False
