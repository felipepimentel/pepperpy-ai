"""Learning error handling utilities."""

from typing import Any, Dict, List, Optional

from . import (
    LearningError,
    InContextError,
    RetrievalError,
    FineTuningError,
)


class ExampleMatchError(InContextError):
    """Error raised when no matching examples are found."""
    
    def __init__(
        self,
        message: str,
        query: str,
        similarity_threshold: float,
        examples_checked: int,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            query: Search query.
            similarity_threshold: Minimum similarity threshold.
            examples_checked: Number of examples checked.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.query = query
        self.similarity_threshold = similarity_threshold
        self.examples_checked = examples_checked
        self.details = details or {}


class ExampleLimitError(InContextError):
    """Error raised when example limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        max_examples: int,
        current_examples: int,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            max_examples: Maximum number of examples.
            current_examples: Current number of examples.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.max_examples = max_examples
        self.current_examples = current_examples
        self.details = details or {}


class RetrievalMatchError(RetrievalError):
    """Error raised when no matching documents are found."""
    
    def __init__(
        self,
        message: str,
        query: str,
        min_similarity: float,
        documents_checked: int,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            query: Search query.
            min_similarity: Minimum similarity threshold.
            documents_checked: Number of documents checked.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.query = query
        self.min_similarity = min_similarity
        self.documents_checked = documents_checked
        self.details = details or {}


class ContextLengthError(RetrievalError):
    """Error raised when context length is exceeded."""
    
    def __init__(
        self,
        message: str,
        max_length: int,
        current_length: int,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            max_length: Maximum context length.
            current_length: Current context length.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.max_length = max_length
        self.current_length = current_length
        self.details = details or {}


class TrainingError(FineTuningError):
    """Error raised during model training."""
    
    def __init__(
        self,
        message: str,
        model: str,
        epoch: int,
        metrics: Dict[str, float],
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            model: Model being trained.
            epoch: Current epoch.
            metrics: Training metrics.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.model = model
        self.epoch = epoch
        self.metrics = metrics
        self.details = details or {}


class ValidationError(FineTuningError):
    """Error raised during model validation."""
    
    def __init__(
        self,
        message: str,
        model: str,
        metrics: Dict[str, float],
        threshold: float,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            model: Model being validated.
            metrics: Validation metrics.
            threshold: Validation threshold.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.model = model
        self.metrics = metrics
        self.threshold = threshold
        self.details = details or {} 