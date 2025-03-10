"""Error classes for the RAG module.

This module defines error classes specific to RAG operations.
"""

from typing import Any, Dict, Optional

from pepperpy.errors import PepperPyError


class RAGError(PepperPyError):
    """Base class for RAG-related errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a RAG error.

        Args:
            message: The error message
            details: Additional details about the error
        """
        super().__init__(message)
        self.details = details or {}


class DocumentError(RAGError):
    """Error raised when there is an issue with a document."""

    pass


class DocumentLoadError(DocumentError):
    """Error raised when there is an issue loading a document."""

    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a document load error.

        Args:
            message: The error message
            source: The source of the document
            details: Additional details about the error
        """
        super().__init__(message, details)
        self.source = source


class DocumentProcessError(DocumentError):
    """Error raised when there is an issue processing a document."""

    pass


class StorageError(RAGError):
    """Error raised when there is an issue with storage."""

    pass


class VectorStoreError(StorageError):
    """Error raised when there is an issue with a vector store."""

    def __init__(
        self,
        message: str,
        store_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a vector store error.

        Args:
            message: The error message
            store_type: The type of vector store
            details: Additional details about the error
        """
        super().__init__(message, details)
        self.store_type = store_type


class PipelineError(RAGError):
    """Error raised when there is an issue with a pipeline."""

    pass


class PipelineStageError(PipelineError):
    """Error raised when there is an issue with a pipeline stage."""

    def __init__(
        self,
        message: str,
        stage_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a pipeline stage error.

        Args:
            message: The error message
            stage_name: The name of the pipeline stage
            details: Additional details about the error
        """
        super().__init__(message, details)
        self.stage_name = stage_name


class QueryError(RAGError):
    """Error raised when there is an issue with a query."""

    pass


class RetrievalError(RAGError):
    """Error raised when there is an issue with retrieval."""

    pass


class GenerationError(RAGError):
    """Error raised when there is an issue with generation."""

    pass
