"""Unified error handling for capabilities.

This module provides a centralized error handling system for all capability-related
operations, replacing the scattered error classes in individual capability modules.
"""

from enum import Enum
from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperpyError


class CapabilityType(Enum):
    """Types of capabilities supported by the system."""

    LEARNING = "learning"
    PLANNING = "planning"
    REASONING = "reasoning"
    MEMORY = "memory"
    PERCEPTION = "perception"
    GENERATION = "generation"
    ANALYSIS = "analysis"


class CapabilityError(PepperpyError):
    """Base error class for capability-related errors.

    This class provides structured error handling for all capability operations,
    with support for error categorization and context tracking.
    """

    def __init__(
        self,
        message: str,
        capability_type: CapabilityType,
        error_code: str = "CAPABILITY_ERROR",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize the capability error.

        Args:
            message: Error message describing what went wrong
            capability_type: Type of capability that encountered the error
            error_code: Specific error code for categorization
            details: Additional error details and context
            cause: Original exception that caused this error

        """
        super().__init__(
            f"{capability_type.value}: {message}",
            error_code=error_code,
            details=details,
        )
        self.capability_type = capability_type
        self.cause = cause


class LearningError(CapabilityError):
    """Error raised by learning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize learning error.

        Args:
            message: Error message
            details: Additional error details
            cause: Original exception

        """
        super().__init__(
            message,
            CapabilityType.LEARNING,
            error_code="LEARNING_ERROR",
            details=details,
            cause=cause,
        )


class PlanningError(CapabilityError):
    """Error raised by planning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize planning error.

        Args:
            message: Error message
            details: Additional error details
            cause: Original exception

        """
        super().__init__(
            message,
            CapabilityType.PLANNING,
            error_code="PLANNING_ERROR",
            details=details,
            cause=cause,
        )


class ReasoningError(CapabilityError):
    """Error raised by reasoning capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize reasoning error.

        Args:
            message: Error message
            details: Additional error details
            cause: Original exception

        """
        super().__init__(
            message,
            CapabilityType.REASONING,
            error_code="REASONING_ERROR",
            details=details,
            cause=cause,
        )


class MemoryError(CapabilityError):
    """Error raised by memory capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize memory error.

        Args:
            message: Error message
            details: Additional error details
            cause: Original exception

        """
        super().__init__(
            message,
            CapabilityType.MEMORY,
            error_code="MEMORY_ERROR",
            details=details,
            cause=cause,
        )


class PerceptionError(CapabilityError):
    """Error raised by perception capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize perception error.

        Args:
            message: Error message
            details: Additional error details
            cause: Original exception

        """
        super().__init__(
            message,
            CapabilityType.PERCEPTION,
            error_code="PERCEPTION_ERROR",
            details=details,
            cause=cause,
        )


class GenerationError(CapabilityError):
    """Error raised by generation capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize generation error.

        Args:
            message: Error message
            details: Additional error details
            cause: Original exception

        """
        super().__init__(
            message,
            CapabilityType.GENERATION,
            error_code="GENERATION_ERROR",
            details=details,
            cause=cause,
        )


class AnalysisError(CapabilityError):
    """Error raised by analysis capabilities."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize analysis error.

        Args:
            message: Error message
            details: Additional error details
            cause: Original exception

        """
        super().__init__(
            message,
            CapabilityType.ANALYSIS,
            error_code="ANALYSIS_ERROR",
            details=details,
            cause=cause,
        )
