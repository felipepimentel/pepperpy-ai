"""Content processors for transforming and analyzing content.

This module provides implementations for processing different types of content:
- ContentProcessor: Base class for content processors
- TextProcessor: Processor for text content with common text operations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pepperpy.content.base import Content
from pepperpy.content.loaders import TextContent


class ContentProcessor(ABC):
    """Base class for content processors."""

    @abstractmethod
    def process(self, content: Content, **kwargs: Any) -> Content:
        """Process content.

        Args:
            content: Content to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Processed content
        """
        pass

    @abstractmethod
    def supports(self, content: Content) -> bool:
        """Check if the processor supports the given content.

        Args:
            content: Content to check

        Returns:
            True if supported, False otherwise
        """
        pass


class TextProcessor(ContentProcessor):
    """Processor for text content with common text operations."""

    def process(
        self, content: Content, *, operations: Optional[List[str]] = None, **kwargs: Any
    ) -> TextContent:
        """Process text content.

        Args:
            content: Text content to process
            operations: List of operations to apply (default: None)
                Supported operations:
                - 'lower': Convert to lowercase
                - 'upper': Convert to uppercase
                - 'strip': Strip whitespace
                - 'normalize': Normalize whitespace
                - 'split': Split into list (returns joined result)
            **kwargs: Additional parameters for operations

        Returns:
            Processed text content

        Raises:
            ValueError: If content is not text or operation is not supported
        """
        if not isinstance(content, TextContent):
            raise ValueError("Content must be TextContent")

        text = content.load()
        operations = operations or []

        for op in operations:
            if op == "lower":
                text = text.lower()
            elif op == "upper":
                text = text.upper()
            elif op == "strip":
                text = text.strip()
            elif op == "normalize":
                text = " ".join(text.split())
            elif op == "split":
                separator = kwargs.get("separator", " ")
                text = separator.join(text.split())
            else:
                raise ValueError(f"Unsupported operation: {op}")

        return TextContent(
            name=f"{content.name}_processed", text=text, metadata=content.metadata
        )

    def supports(self, content: Content) -> bool:
        """Check if the content is supported.

        Args:
            content: Content to check

        Returns:
            True if content is TextContent
        """
        return isinstance(content, TextContent)


class TextAnalyzer(ContentProcessor):
    """Analyzer for text content that extracts metrics and statistics."""

    def process(
        self, content: Content, *, metrics: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Analyze text content.

        Args:
            content: Text content to analyze
            metrics: List of metrics to compute (default: None)
                Supported metrics:
                - 'length': Text length in characters
                - 'words': Word count
                - 'sentences': Sentence count
                - 'lines': Line count
                - 'avg_word_length': Average word length
                - 'avg_sentence_length': Average sentence length
            **kwargs: Additional parameters for analysis

        Returns:
            Dictionary of computed metrics

        Raises:
            ValueError: If content is not text or metric is not supported
        """
        if not isinstance(content, TextContent):
            raise ValueError("Content must be TextContent")

        text = content.load()
        metrics = metrics or ["length", "words", "sentences", "lines"]
        results = {}

        for metric in metrics:
            if metric == "length":
                results["length"] = len(text)
            elif metric == "words":
                results["words"] = len(text.split())
            elif metric == "sentences":
                # Simple sentence splitting by punctuation
                results["sentences"] = len([
                    s.strip() for s in text.split(".") if s.strip()
                ])
            elif metric == "lines":
                results["lines"] = len(text.splitlines())
            elif metric == "avg_word_length":
                words = [w for w in text.split() if w]
                results["avg_word_length"] = (
                    sum(len(w) for w in words) / len(words) if words else 0
                )
            elif metric == "avg_sentence_length":
                sentences = [s.strip() for s in text.split(".") if s.strip()]
                results["avg_sentence_length"] = (
                    sum(len(s.split()) for s in sentences) / len(sentences)
                    if sentences
                    else 0
                )
            else:
                raise ValueError(f"Unsupported metric: {metric}")

        return results

    def supports(self, content: Content) -> bool:
        """Check if the content is supported.

        Args:
            content: Content to check

        Returns:
            True if content is TextContent
        """
        return isinstance(content, TextContent)
