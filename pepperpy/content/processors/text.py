"""Text processor for content capability."""

import re
from typing import Any, Dict, List, Optional, Union

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from pepperpy.content.base import ContentError, ContentItem, ContentProcessor


class TextProcessorConfig(BaseModel):
    """Configuration for text processor."""

    min_length: int = Field(default=50, description="Minimum content length")
    max_length: Optional[int] = Field(
        default=None, description="Maximum content length"
    )
    remove_html: bool = Field(default=True, description="Remove HTML tags from content")
    normalize_whitespace: bool = Field(
        default=True, description="Normalize whitespace in content"
    )
    calculate_metrics: bool = Field(
        default=True, description="Calculate text metrics (word count, read time)"
    )


class TextProcessor(ContentProcessor):
    """Text processor implementation."""

    def __init__(self, **config: Any):
        """Initialize processor with configuration.

        Args:
            **config: Configuration parameters

        Raises:
            ContentError: If configuration is invalid
        """
        try:
            self.config = TextProcessorConfig(**config)
        except Exception as e:
            raise ContentError(
                "Failed to initialize text processor",
                details={"error": str(e)},
            )

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        soup = BeautifulSoup(text, features="html.parser")
        return soup.get_text(separator=" ", strip=True)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Replace multiple whitespace with single space
        text = re.sub(r"\s+", " ", text)
        # Remove whitespace around punctuation
        text = re.sub(r"\s*([,.!?])\s*", r"\1 ", text)
        # Normalize quotes
        text = re.sub(r"[" "'']", '"', text)
        return text.strip()

    def _calculate_metrics(self, text: str) -> Dict[str, Any]:
        """Calculate text metrics.

        Args:
            text: Text to analyze

        Returns:
            Dictionary of metrics
        """
        # Count words (simple implementation)
        words = len(text.split())

        # Estimate read time (average 200 words per minute)
        read_time = max(1, round(words / 200))

        return {
            "word_count": words,
            "read_time": read_time,
        }

    async def process(
        self,
        items: Union[ContentItem, List[ContentItem]],
        **kwargs: Any,
    ) -> Union[ContentItem, List[ContentItem]]:
        """Process content items.

        Args:
            items: Single item or list of items to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Processed item(s)

        Raises:
            ContentError: If processing fails
        """
        try:
            # Convert single item to list for uniform processing
            items_list = [items] if isinstance(items, ContentItem) else items

            processed = []
            for item in items_list:
                content = item.content

                # Remove HTML if configured
                if self.config.remove_html:
                    content = self._clean_html(content)

                # Normalize whitespace if configured
                if self.config.normalize_whitespace:
                    content = self._normalize_whitespace(content)

                # Apply length limits
                if len(content) < self.config.min_length:
                    continue
                if self.config.max_length:
                    content = content[: self.config.max_length]

                # Calculate metrics if configured
                if self.config.calculate_metrics:
                    metrics = self._calculate_metrics(content)
                    item.metadata.word_count = metrics["word_count"]
                    item.metadata.read_time = metrics["read_time"]

                # Update content
                item.content = content
                processed.append(item)

            # Return single item or list based on input type
            return processed[0] if isinstance(items, ContentItem) else processed

        except Exception as e:
            raise ContentError(
                "Failed to process content",
                details={"error": str(e)},
            )
