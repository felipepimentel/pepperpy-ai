"""Monitoring errors module for the Pepperpy framework.

This module defines monitoring-related errors used throughout the framework.
"""

from pepperpy.core.errors import MonitoringError


class CollectorError(MonitoringError):
    """Error raised when a collector operation fails."""


class ExporterError(MonitoringError):
    """Error raised when an exporter operation fails."""


class AlertError(MonitoringError):
    """Error raised when an alert operation fails."""


class RuleError(MonitoringError):
    """Error raised when a rule operation fails."""


class ValidationError(MonitoringError):
    """Error raised when monitoring validation fails."""


# Export public API
__all__ = [
    "AlertError",
    "CollectorError",
    "ExporterError",
    "RuleError",
    "ValidationError",
] 