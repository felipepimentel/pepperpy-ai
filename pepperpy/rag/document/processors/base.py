"""Base document processor module.

This module provides the base class for document processors.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Union

from pepperpy.rag.document.types import Document


class BaseDocumentProcessor(ABC):
    """Base class for document processors.

    Document processors are responsible for preprocessing and transforming documents
    before they are used in the RAG pipeline. This can include tasks such as:
    - Text cleaning and normalization
    - Language detection and translation
    - Content filtering and validation
    - Metadata enrichment
    - Document chunking and splitting
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the document processor.

        Args:
            **kwargs: Additional keyword arguments for the processor.
        """
        self.kwargs = kwargs

    @abstractmethod
    async def process(
        self,
        documents: Union[Document, List[Document]],
        **kwargs: Any,
    ) -> Union[Document, List[Document]]:
        """Process one or more documents.

        Args:
            documents: A single document or list of documents to process.
            **kwargs: Additional keyword arguments for processing.

        Returns:
            The processed document(s).

        Raises:
            DocumentProcessError: If an error occurs during processing.
        """
        pass

    def __repr__(self) -> str:
        """Return a string representation of the processor."""
        return f"{self.__class__.__name__}(**{self.kwargs})"
