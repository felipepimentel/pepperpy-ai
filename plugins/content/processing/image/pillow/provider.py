"""Pillow image processing provider."""

from pathlib import Path
from typing import Any

from PIL import Image

from pepperpy.content.base import ContentProcessor, ProcessingResult
from pepperpy.core.errors import ProviderError
from pepperpy.plugins.plugin import ProviderPlugin


class PillowProvider(ContentProcessor, ProviderPlugin):
    """Pillow image processing provider."""

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
        """Process image.

        Args:
            content: Path to image
            **kwargs: Additional arguments

        Returns:
            Processing result with image metadata

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

            # Open image
            with Image.open(content) as img:
                # Extract metadata
                metadata = {
                    "filename": content.name,
                    "format": img.format,
                    "size": img.size,
                    "mode": img.mode,
                }

                # For this example, we'll just return a description of the image
                text = f"Image: {content.name}\nFormat: {img.format}\nSize: {img.size}\nMode: {img.mode}"

                return ProcessingResult(text=text, metadata=metadata)

        except Exception as e:
            raise ProviderError(f"Failed to process image: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False
