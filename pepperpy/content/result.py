"""
PepperPy Content Results.

Result classes specific to content processing.
"""

import json
from pathlib import Path
from typing import Any, Optional

from pepperpy.common.result import Result, ResultError


class TextResult(Result):
    """Result containing text content."""

    def __init__(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        logger: Optional = None,
    ):
        """Initialize a text result.

        Args:
            content: Text content
            metadata: Optional metadata
            logger: Optional logger
        """
        super().__init__(content, metadata, logger)

    def tokenize(self) -> list[str]:
        """Split the text into tokens."""
        return self.content.split()

    def word_count(self) -> int:
        """Count words in the text."""
        return len(self.tokenize())


class JSONResult(Result):
    """Result containing JSON content."""

    def __init__(
        self,
        content: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        logger: Optional = None,
    ):
        """Initialize a JSON result.

        Args:
            content: JSON content as dictionary
            metadata: Optional metadata
            logger: Optional logger
        """
        super().__init__(content, metadata, logger)

    def __str__(self) -> str:
        """Format JSON content as a string."""
        return json.dumps(self.content, indent=2)

    def save(
        self, path: str | Path, header: str | None = None, encoding: str = "utf-8"
    ) -> Path:
        """Save the JSON result to a file.

        Args:
            path: Path to save the result
            header: Optional header as a comment
            encoding: File encoding

        Returns:
            Path to the saved file
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding=encoding) as f:
                if header:
                    f.write(f"// {header}\n")
                json.dump(self.content, f, indent=2)

            self.logger.info(f"JSON result saved to {path}")
            return path
        except Exception as e:
            raise ResultError(f"Failed to save JSON result: {e!s}", cause=e)


class DocumentResult(Result):
    """Result containing processed document content."""

    def __init__(
        self,
        content: str,
        document_type: str,
        source_path: Path | None = None,
        metadata: dict[str, Any] | None = None,
        logger: Optional = None,
    ):
        """Initialize a document result.

        Args:
            content: Document content
            document_type: Type of document (pdf, markdown, etc.)
            source_path: Optional source file path
            metadata: Optional metadata
            logger: Optional logger
        """
        metadata = metadata or {}
        metadata["document_type"] = document_type
        if source_path:
            metadata["source_path"] = str(source_path)

        super().__init__(content, metadata, logger)
        self.document_type = document_type
        self.source_path = source_path
