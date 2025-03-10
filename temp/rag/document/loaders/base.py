"""Base document loader implementation.

This module provides the base class for document loaders.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.errors import DocumentLoadError
from pepperpy.rag.storage.types import Document


class BaseDocumentLoader(ABC):
    """Base class for document loaders.

    This class defines the interface for loading documents from various sources.
    Subclasses must implement the _load_from_file and _load_from_string methods.
    """

    def __init__(
        self, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        """Initialize the document loader.

        Args:
            metadata: Optional metadata to associate with loaded documents.
            **kwargs: Additional keyword arguments.
        """
        self.metadata = metadata or {}

    @abstractmethod
    async def _load_from_file(
        self,
        file_path: Union[str, Path],
        **kwargs: Any,
    ) -> List[Document]:
        """Load documents from a file.

        Args:
            file_path: Path to the file to load.
            **kwargs: Additional arguments.

        Returns:
            List of loaded documents.

        Raises:
            DocumentLoadError: If loading fails.
        """
        ...

    @abstractmethod
    async def _load_from_string(
        self,
        content: str,
        **kwargs: Any,
    ) -> List[Document]:
        """Load documents from a string.

        Args:
            content: String content to load.
            **kwargs: Additional arguments.

        Returns:
            List of loaded documents.

        Raises:
            DocumentLoadError: If loading fails.
        """
        ...

    async def load(
        self,
        source: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Load documents from a source.

        Args:
            source: File path or string content to load.
            metadata: Optional metadata to merge with loader metadata.
            **kwargs: Additional arguments.

        Returns:
            List of loaded documents.

        Raises:
            DocumentLoadError: If loading fails.
        """
        try:
            # Merge metadata
            combined_metadata = {**self.metadata}
            if metadata:
                combined_metadata.update(metadata)

            # Load from file if source is a path
            if isinstance(source, (str, Path)) and Path(source).is_file():
                documents = await self._load_from_file(source, **kwargs)
            else:
                # Otherwise treat as string content
                documents = await self._load_from_string(str(source), **kwargs)

            # Add metadata to documents
            for doc in documents:
                if combined_metadata:
                    doc_metadata = doc.metadata or {}
                    doc_metadata.update(combined_metadata)
                    doc.metadata = doc_metadata

            return documents

        except Exception as e:
            raise DocumentLoadError(f"Error loading document: {str(e)}") from e

    def __repr__(self) -> str:
        """Get string representation of the loader.

        Returns:
            String representation.
        """
        return f"{self.__class__.__name__}(metadata={self.metadata})"
