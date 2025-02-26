"""Observability management.

This module provides centralized management of observability components.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from pepperpy.core.observability.collector import MetricsCollector
from pepperpy.core.observability.correlation import CorrelationManager
from pepperpy.core.observability.health import HealthChecker
from pepperpy.core.observability.tracing import Tracer


@dataclass
class ObservabilityConfig:
    """Configuration for the observability system."""

    # Logging configuration
    log_level: int = logging.INFO
    log_format: str = "json"  # "json" or "text"
    log_handlers: list[logging.Handler] = field(default_factory=list)

    # Metrics configuration
    enable_metrics: bool = True
    metrics_prefix: str | None = None

    # Tracing configuration
    enable_tracing: bool = True

    # Health check configuration
    enable_health_checks: bool = True
    health_check_timeout: float = 5.0

    # Error tracking configuration
    sentry_dsn: str | None = None
    environment: str = "development"


class ObservabilityManager:
    """Centralized manager for all observability components."""

    _instance = None

    def __new__(
        cls, config: ObservabilityConfig | None = None
    ) -> "ObservabilityManager":
        """Create or get singleton instance.

        Args:
            config: Optional configuration

        Returns:
            ObservabilityManager instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self, config: ObservabilityConfig | None = None) -> None:
        """Initialize manager.

        Args:
            config: Optional configuration
        """
        # Skip if already initialized
        if getattr(self, "__initialized", False):
            return

        # Set configuration
        self.config = config or ObservabilityConfig()

        # Initialize components
        self._setup_logging()
        self._setup_metrics()
        self._setup_tracing()
        self._setup_health_checks()
        self._setup_error_tracking()

        # Mark as initialized
        self.__initialized = True

    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.log_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Add configured handlers
        if self.config.log_handlers:
            for handler in self.config.log_handlers:
                root_logger.addHandler(handler)
        else:
            # Add default handler
            handler = logging.StreamHandler()
            if self.config.log_format == "json":
                from pepperpy.core.observability.logging import JsonFormatter

                handler.setFormatter(JsonFormatter())
            else:
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )
                )
            root_logger.addHandler(handler)

    def _setup_metrics(self) -> None:
        """Set up metrics collection."""
        self.metrics = MetricsCollector()

    def _setup_tracing(self) -> None:
        """Set up distributed tracing."""
        self.tracer = Tracer()
        self.correlation = CorrelationManager()

    def _setup_health_checks(self) -> None:
        """Set up health checks."""
        self.health = HealthChecker()

    def _setup_error_tracking(self) -> None:
        """Set up error tracking."""
        if self.config.sentry_dsn:
            try:
                import sentry_sdk

                sentry_sdk.init(
                    dsn=self.config.sentry_dsn,
                    environment=self.config.environment,
                )
            except ImportError:
                logging.warning("Sentry SDK not installed. Error tracking disabled.")

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log info message.

        Args:
            msg: Message to log
            *args: Format args
            **kwargs: Format kwargs
        """
        logging.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log warning message.

        Args:
            msg: Message to log
            *args: Format args
            **kwargs: Format kwargs
        """
        logging.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, exc_info: bool = True, **kwargs: Any) -> None:
        """Log error message.

        Args:
            msg: Message to log
            *args: Format args
            exc_info: Whether to include exception info
            **kwargs: Format kwargs
        """
        logging.error(msg, *args, exc_info=exc_info, **kwargs)

    def track_metric(
        self, name: str, value: float = 1.0, tags: dict[str, str] | None = None
    ) -> None:
        """Track a metric.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional metric tags
        """
        if self.config.enable_metrics:
            self.metrics.increment(name, tags)

    def start_trace(self, name: str, context: dict[str, Any] | None = None) -> Any:
        """Start a trace span.

        Args:
            name: Span name
            context: Optional span context

        Returns:
            Trace span
        """
        if self.config.enable_tracing:
            return self.tracer.start_span(name, context)
        return None

    def end_trace(self) -> None:
        """End the current trace span."""
        if self.config.enable_tracing:
            self.tracer.end_span()

    async def check_health(self) -> dict[str, dict[str, Any]]:
        """Run health checks.

        Returns:
            Health check results
        """
        if self.config.enable_health_checks:
            return await self.health.check_all()
        return {"status": "disabled"}


__all__ = ["ObservabilityConfig", "ObservabilityManager"]
