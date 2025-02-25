"""Observability system for the Pepperpy framework.

This module provides functionality for logging, error tracking, and
monitoring application behavior.
"""

import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Optional

from pepperpy.core.config import ConfigModel
from pepperpy.core.metrics import metrics_manager


class ObservabilityConfig(ConfigModel):
    """Configuration for the observability system."""

    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_file_logging: bool = False
    log_file: str = "pepperpy.log"
    enable_sentry: bool = False
    sentry_dsn: str | None = None


class ObservabilityManager:
    """Manager for logging and error tracking."""

    _instance: Optional["ObservabilityManager"] = None

    def __init__(self) -> None:
        """Initialize the observability manager."""
        self.config = ObservabilityConfig()
        self._logger = logging.getLogger("pepperpy")
        self._metrics = metrics_manager
        self._setup_logging()

    @classmethod
    def get_instance(cls) -> "ObservabilityManager":
        """Get singleton instance.

        Returns:
            ObservabilityManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        # Set log level
        level = getattr(logging, self.config.log_level.upper())
        self._logger.setLevel(level)

        # Create console handler
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter(self.config.log_format))
        self._logger.addHandler(console)

        # Create file handler if enabled
        if self.config.enable_file_logging:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setFormatter(logging.Formatter(self.config.log_format))
            self._logger.addHandler(file_handler)

        # Set up Sentry if enabled
        if self.config.enable_sentry and self.config.sentry_dsn:
            try:
                import sentry_sdk

                sentry_sdk.init(dsn=self.config.sentry_dsn)
            except ImportError:
                self.log_warning(
                    "observability.sentry",
                    "Sentry SDK not installed. Error tracking disabled.",
                )

    def log_info(
        self, source: str, message: str, context: dict[str, Any] | None = None
    ) -> None:
        """Log an informational message.

        Args:
            source: Source of the log message
            message: Log message
            context: Optional context dictionary
        """
        self._logger.info(f"[{source}] {message}")
        if context:
            self._logger.info(f"Context: {context}")

        self._metrics.counter(
            "log_messages",
            "Number of log messages",
            labels={"level": "info", "source": source},
        ).inc()

    def log_warning(
        self,
        source: str,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log a warning message.

        Args:
            source: Source of the warning
            message: Warning message
            context: Optional context dictionary
        """
        self._logger.warning(f"[{source}] {message}")
        if context:
            self._logger.warning(f"Context: {context}")

        self._metrics.counter(
            "log_messages",
            "Number of log messages",
            labels={"level": "warning", "source": source},
        ).inc()

    def log_error(
        self,
        source: str,
        message: str,
        exception: Exception | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log an error message.

        Args:
            source: Source of the error
            message: Error message
            exception: Optional exception object
            context: Optional context dictionary
        """
        self._logger.error(f"[{source}] {message}")
        if exception:
            self._logger.error(f"Exception: {exception}")
            self._logger.error(f"Traceback: {traceback.format_exc()}")
        if context:
            self._logger.error(f"Context: {context}")

        self._metrics.counter(
            "log_messages",
            "Number of log messages",
            labels={"level": "error", "source": source},
        ).inc()

        # Track error in Sentry if enabled
        if self.config.enable_sentry and self.config.sentry_dsn:
            try:
                import sentry_sdk

                with sentry_sdk.push_scope() as scope:
                    scope.set_tag("source", source)
                    if context:
                        scope.set_context("additional", context)
                    if exception:
                        sentry_sdk.capture_exception(exception)
                    else:
                        sentry_sdk.capture_message(message)
            except ImportError:
                pass

    def track_timing(self, source: str, operation: str, duration: float) -> None:
        """Track operation timing.

        Args:
            source: Source of the timing
            operation: Operation being timed
            duration: Duration in seconds
        """
        self._metrics.histogram(
            "operation_duration",
            "Operation duration in seconds",
            labels={"source": source, "operation": operation},
        ).observe(duration)

    def track_value(self, source: str, name: str, value: float) -> None:
        """Track a value.

        Args:
            source: Source of the value
            name: Name of the value
            value: Value to track
        """
        self._metrics.gauge(
            "tracked_value",
            "Tracked value",
            labels={"source": source, "name": name},
        ).set(value)


# Global observability manager instance
observability_manager = ObservabilityManager()


__all__ = [
    "ObservabilityConfig",
    "ObservabilityManager",
    "observability_manager",
]
