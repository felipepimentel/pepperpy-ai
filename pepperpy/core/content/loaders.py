"""Content loaders for different content types.

This module provides implementations for loading different types of content:
- ContentLoader: Base class for content loaders
- TextContentLoader: Loader for text content
- FileContentLoader: Loader for file content
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Union

from pepperpy.content.base import Content, ContentMetadata, ContentType


class ContentLoader(ABC):
    """Base class for content loaders."""

    @abstractmethod
    def load(self, source: Any, **kwargs: Any) -> Content:
        """Load content from a source.

        Args:
            source: Content source
            **kwargs: Additional loader-specific parameters

        Returns:
            Loaded content
        """
        pass

    @abstractmethod
    def supports(self, source: Any) -> bool:
        """Check if the loader supports the given source.

        Args:
            source: Content source to check

        Returns:
            True if supported, False otherwise
        """
        pass


class TextContent(Content):
    """Text content implementation."""

    def __init__(
        self, name: str, text: str, metadata: Optional[ContentMetadata] = None
    ):
        """Initialize text content.

        Args:
            name: Name of the content
            text: Text content
            metadata: Optional content metadata
        """
        super().__init__(ContentType.TEXT, name, text, metadata)

    def _calculate_size(self) -> int:
        """Calculate the size of the text in bytes."""
        return len(self.data.encode("utf-8"))

    def load(self) -> str:
        """Load the text content.

        Returns:
            The text content
        """
        return self.data

    def save(self, path: Union[str, Path]) -> None:
        """Save the text content to a file.

        Args:
            path: Path to save the content to
        """
        path = Path(path)
        path.write_text(self.data, encoding="utf-8")


class TextContentLoader(ContentLoader):
    """Loader for text content."""

    def load(self, source: Union[str, Path], **kwargs: Any) -> TextContent:
        """Load text content from a string or file.

        Args:
            source: Text string or path to text file
            **kwargs: Additional parameters (encoding, etc.)

        Returns:
            Loaded text content
        """
        if isinstance(source, Path) or (
            isinstance(source, str) and Path(source).exists()
        ):
            path = Path(source)
            name = path.name
            text = path.read_text(encoding=kwargs.get("encoding", "utf-8"))
        else:
            name = kwargs.get("name", "text")
            text = str(source)

        return TextContent(name, text)

    def supports(self, source: Any) -> bool:
        """Check if the source is supported.

        Args:
            source: Content source to check

        Returns:
            True if source is string or path to text file
        """
        return isinstance(source, (str, Path))


class FileContent(Content):
    """File content implementation."""

    def __init__(
        self,
        name: str,
        path: Union[str, Path],
        metadata: Optional[ContentMetadata] = None,
    ):
        """Initialize file content.

        Args:
            name: Name of the content
            path: Path to the file
            metadata: Optional content metadata
        """
        self.path = Path(path)
        super().__init__(ContentType.FILE, name, None, metadata)

    def _calculate_size(self) -> int:
        """Calculate the size of the file in bytes."""
        return self.path.stat().st_size

    def load(self) -> bytes:
        """Load the file content.

        Returns:
            The file content as bytes
        """
        return self.path.read_bytes()

    def save(self, path: Union[str, Path]) -> None:
        """Save the file content to a new location.

        Args:
            path: Path to save the content to
        """
        from shutil import copy2

        copy2(self.path, path)


class FileContentLoader(ContentLoader):
    """Loader for file content."""

    def load(self, source: Union[str, Path], **kwargs: Any) -> FileContent:
        """Load content from a file.

        Args:
            source: Path to the file
            **kwargs: Additional parameters

        Returns:
            Loaded file content
        """
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return FileContent(path.name, path)

    def supports(self, source: Any) -> bool:
        """Check if the source is supported.

        Args:
            source: Content source to check

        Returns:
            True if source is a path to an existing file
        """
        if isinstance(source, (str, Path)):
            return Path(source).exists()
        return False
