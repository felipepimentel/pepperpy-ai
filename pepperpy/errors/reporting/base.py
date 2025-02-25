"""Base classes for error reporting.

This module provides the core error reporting functionality, including:
- Error report data structure
- Report formatters
- Multiple reporting destinations

Example:
    >>> error = ValidationError("Invalid input")
    >>> reporter = CompositeReporter([
    ...     ConsoleReporter(),
    ...     FileReporter("errors.log")
    ... ])
    >>> reporter.report(error)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import logging
from ..base import PepperpyError

logger = logging.getLogger(__name__)

@dataclass
class ErrorReport:
    """Container for error report data.
    
    Args:
        error: The error being reported
        context: Additional context about the error
        stack_trace: Stack trace from the error
        timestamp: When the error occurred
        handled: Whether the error was handled
        recovery_attempted: Whether recovery was attempted
        recovery_successful: Whether recovery succeeded
    
    Example:
        >>> error = ValidationError("Invalid input")
        >>> report = ErrorReport(
        ...     error=error,
        ...     context={"request_id": "123"},
        ...     stack_trace=error.stack_trace,
        ...     timestamp=datetime.now(),
        ...     handled=True,
        ...     recovery_attempted=True,
        ...     recovery_successful=True
        ... )
        >>> report.to_json()
        '{"error_type": "ValidationError", ...}'
    """
    
    error: PepperpyError
    context: Dict[str, Any]
    stack_trace: str
    timestamp: datetime
    handled: bool
    recovery_attempted: bool
    recovery_successful: Optional[bool]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the report to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the report
        """
        return {
            "error_type": self.error.__class__.__name__,
            "error_message": str(self.error),
            "error_code": self.error.code,
            "context": self.context,
            "stack_trace": self.stack_trace,
            "timestamp": self.timestamp.isoformat(),
            "handled": self.handled,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful
        }
    
    def to_json(self) -> str:
        """Convert the report to JSON.
        
        Returns:
            str: JSON representation of the report
        """
        return json.dumps(self.to_dict(), indent=2)

class ErrorReporter(ABC):
    """Abstract base class for error reporters.
    
    Example:
        >>> class MyReporter(ErrorReporter):
        ...     def report(self, error_report):
        ...         print(error_report.to_json())
    """
    
    @abstractmethod
    def report(self, error_report: ErrorReport) -> None:
        """Report an error.
        
        Args:
            error_report: The error report to process
        """
        pass

class ConsoleReporter(ErrorReporter):
    """Reporter that outputs errors to the console.
    
    Example:
        >>> reporter = ConsoleReporter()
        >>> reporter.report(error_report)
        === Error Report ===
        {
          "error_type": "ValidationError",
          ...
        }
    """
    
    def report(self, error_report: ErrorReport) -> None:
        """Report an error to the console."""
        print("=== Error Report ===")
        print(error_report.to_json())
        print("==================")

class FileReporter(ErrorReporter):
    """Reporter that writes errors to a file.
    
    Args:
        filepath: Path to the error log file
    
    Example:
        >>> reporter = FileReporter("errors.log")
        >>> reporter.report(error_report)
    """
    
    def __init__(self, filepath: str):
        """Initialize a new file reporter."""
        self.filepath = filepath
        
    def report(self, error_report: ErrorReport) -> None:
        try:
            with open(self.filepath, "a") as f:
                f.write(f"{error_report.to_json()}
")
        except Exception as e:
            logger.error(f"Failed to write error report to file: {e}")

class LoggingReporter(ErrorReporter):
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
    def report(self, error_report: ErrorReport) -> None:
        self.logger.error(
            "Error occurred",
            extra={
                "error_report": error_report.to_dict()
            }
        )

class CompositeReporter(ErrorReporter):
    def __init__(self, reporters: Optional[List[ErrorReporter]] = None):
        self.reporters = reporters or []
        
    def add_reporter(self, reporter: ErrorReporter) -> None:
        self.reporters.append(reporter)
        
    def report(self, error_report: ErrorReport) -> None:
        for reporter in self.reporters:
            try:
                reporter.report(error_report)
            except Exception as e:
                logger.error(f"Reporter {reporter.__class__.__name__} failed: {e}")

global_error_reporter = CompositeReporter([
    ConsoleReporter(),
    LoggingReporter()
])