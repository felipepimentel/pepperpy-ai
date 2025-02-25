"""Exception classes for the observability system."""

from typing import Optional


class ObservabilityError(Exception):
    """Base class for all observability-related errors."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause


class MetricsError(ObservabilityError):
    """Raised when there is an error with metrics collection or export."""
    pass


class LoggingError(ObservabilityError):
    """Raised when there is an error with logging operations."""
    pass


class TracingError(ObservabilityError):
    """Raised when there is an error with tracing operations."""
    pass


class HealthCheckError(ObservabilityError):
    """Raised when there is an error with health checks."""
    pass


class CorrelationError(ObservabilityError):
    """Raised when there is an error with context correlation."""
    pass


class ExporterError(ObservabilityError):
    """Raised when there is an error exporting observability data."""
    pass


class ConfigurationError(ObservabilityError):
    """Raised when there is an error in observability configuration."""
    pass


class ValidationError(ObservabilityError):
    """Raised when there is an error validating observability data."""
    pass
