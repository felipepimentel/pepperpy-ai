"""Tests for the Pepperpy error handling system.

This module contains comprehensive tests for all components of the error
handling system including error classes, handlers, recovery strategies,
and reporting mechanisms.
"""

from datetime import datetime

from pepperpy.errors import (
    CompositeReporter,
    ConfigurationError,
    ConsoleReporter,
    ErrorCategory,
    ErrorHandler,
    ErrorHandlerRegistry,
    ErrorReport,
    ErrorSeverity,
    FallbackStrategy,
    FileReporter,
    LoggingReporter,
    PepperpyError,
    ResourceError,
    RetryStrategy,
    StateError,
    ValidationError,
    generate_error_code,
    global_error_registry,
    handle_error,
    report_error,
)


def test_error_code_generation():
    """Test error code generation functionality."""
    code = generate_error_code(ErrorCategory.VALIDATION, ErrorSeverity.ERROR, 1)
    assert code == "VAL-E-001"

    code = generate_error_code(ErrorCategory.RESOURCE, ErrorSeverity.CRITICAL, 42)
    assert code == "RES-C-042"


def test_pepperpy_error():
    """Test base error class functionality."""
    error = PepperpyError(
        message="Test error",
        code="TEST-001",
        details={"key": "value"},
        recovery_hint="Try again",
    )

    assert (
        str(error)
        == "[TEST-001] Test error | Recovery hint: Try again | Details: {'key': 'value'}"
    )
    assert error.message == "Test error"
    assert error.code == "TEST-001"
    assert error.details == {"key": "value"}
    assert error.recovery_hint == "Try again"
    assert error.timestamp is not None
    assert error.stack_trace is not None


def test_specific_errors():
    """Test specialized error classes."""
    validation_error = ValidationError("Invalid input")
    assert isinstance(validation_error, PepperpyError)
    assert validation_error.ERROR_CODE_PREFIX == "VAL"

    resource_error = ResourceError("Resource not found")
    assert isinstance(resource_error, PepperpyError)
    assert resource_error.ERROR_CODE_PREFIX == "RES"

    config_error = ConfigurationError("Invalid config")
    assert isinstance(config_error, PepperpyError)
    assert config_error.ERROR_CODE_PREFIX == "CFG"

    state_error = StateError("Invalid state")
    assert isinstance(state_error, PepperpyError)
    assert state_error.ERROR_CODE_PREFIX == "STA"


def test_error_handler():
    """Test error handler registration and execution."""

    class TestHandler(ErrorHandler):
        def __init__(self):
            self.handled = False

        def can_handle(self, error):
            return isinstance(error, ValidationError)

        def handle(self, error):
            self.handled = True
            return True

    registry = ErrorHandlerRegistry()
    handler = TestHandler()
    registry.register(ValidationError, handler)

    error = ValidationError("Test error")
    assert registry.handle(error) is True
    assert handler.handled is True

    registry.unregister(ValidationError, handler)
    assert registry.handle(error) is False


def test_retry_strategy():
    """Test retry recovery strategy with success and failure cases."""

    def failing_operation():
        raise ResourceError("Resource locked")

    def succeeding_operation():
        return True

    strategy = RetryStrategy(max_retries=2, delay=0.1, operation=failing_operation)
    error = ResourceError("Resource locked")

    assert strategy.can_recover(error) is True
    assert strategy.recover(error) is False  # Should fail after retries

    strategy = RetryStrategy(max_retries=2, delay=0.1, operation=succeeding_operation)
    assert strategy.recover(error) is True  # Should succeed


def test_fallback_strategy():
    """Test fallback recovery strategy with primary and backup operations."""

    def primary_operation():
        raise ResourceError("Primary failed")

    def backup_operation():
        return True

    strategy = FallbackStrategy([primary_operation, backup_operation])
    error = ResourceError("Test error")

    assert strategy.can_recover(error) is True
    assert strategy.recover(error) is True  # Should succeed with backup


def test_error_report():
    """Test error report generation and serialization."""
    error = PepperpyError("Test error")
    report = ErrorReport(
        error=error,
        context={"test": True},
        stack_trace=error.stack_trace,
        timestamp=datetime.now(),
        handled=False,
        recovery_attempted=False,
        recovery_successful=None,
    )

    report_dict = report.to_dict()
    assert report_dict["error_type"] == "PepperpyError"
    assert report_dict["error_message"] == "Test error"
    assert report_dict["context"] == {"test": True}
    assert report_dict["handled"] is False
    assert report_dict["recovery_attempted"] is False
    assert report_dict["recovery_successful"] is None

    json_str = report.to_json()
    assert isinstance(json_str, str)
    assert "PepperpyError" in json_str


def test_error_reporters(tmp_path):
    """Test various error reporter implementations."""
    error = ValidationError("Test error")
    report = ErrorReport(
        error=error,
        context={"test": True},
        stack_trace=error.stack_trace,
        timestamp=datetime.now(),
        handled=False,
        recovery_attempted=False,
        recovery_successful=None,
    )

    console_reporter = ConsoleReporter()
    console_reporter.report(report)  # Should print to console

    log_file = tmp_path / "errors.log"
    file_reporter = FileReporter(str(log_file))
    file_reporter.report(report)

    assert log_file.exists()
    content = log_file.read_text()
    assert "ValidationError" in content

    logging_reporter = LoggingReporter()
    logging_reporter.report(report)  # Should log using logging system

    composite = CompositeReporter([ConsoleReporter(), FileReporter(str(log_file))])
    composite.report(report)  # Should report to both console and file


def test_global_error_handling():
    """Test global error handling and reporting functions."""
    error = ValidationError("Test error")

    report = report_error(error, {"test": True})
    assert isinstance(report, ErrorReport)
    assert report.error == error
    assert report.context == {"test": True}

    class TestHandler(ErrorHandler):
        def can_handle(self, error):
            return isinstance(error, ValidationError)

        def handle(self, error):
            return True

    handler = TestHandler()
    global_error_registry.register(ValidationError, handler)
    assert handle_error(error) is True
