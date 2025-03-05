"""Model performance metrics module.

This module provides classes and utilities for tracking and analyzing
model performance metrics, including latency, token usage, and costs.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel


class ModelCallType(str, Enum):
    """Types of model calls."""

    COMPLETION = "completion"
    CHAT = "chat"
    EMBEDDING = "embedding"
    IMAGE = "image"
    AUDIO = "audio"
    OTHER = "other"


@dataclass
class ModelCallEvent:
    """Represents a single model call event.

    Attributes:
        model_id: Identifier of the model used
        provider: Provider of the model (e.g., "openai", "anthropic")
        call_type: Type of model call
        timestamp: When the call was made
        duration_ms: Duration of the call in milliseconds
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        success: Whether the call was successful
        error: Error message if the call failed
        metadata: Additional metadata about the call
    """

    model_id: str
    provider: str
    call_type: ModelCallType
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dictionary representation of the event
        """
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "call_type": self.call_type.value,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }


class ModelMetrics(BaseModel):
    """Aggregated metrics for model performance.

    Attributes:
        total_calls: Total number of calls made
        successful_calls: Number of successful calls
        failed_calls: Number of failed calls
        total_tokens: Total number of tokens processed
        total_input_tokens: Total number of input tokens
        total_output_tokens: Total number of output tokens
        avg_latency_ms: Average latency in milliseconds
        p95_latency_ms: 95th percentile latency in milliseconds
        p99_latency_ms: 99th percentile latency in milliseconds
        estimated_cost: Estimated cost of the calls
    """

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: Optional[float] = None
    p99_latency_ms: Optional[float] = None
    estimated_cost: float = 0.0


class PerformanceAnalyzer:
    """Analyzes model performance metrics.

    This class provides methods for analyzing model performance metrics,
    including calculating aggregated metrics and generating reports.
    """

    def __init__(self):
        """Initialize the performance analyzer."""
        self.events: List[ModelCallEvent] = []

    def add_event(self, event: ModelCallEvent) -> None:
        """Add a model call event to the analyzer.

        Args:
            event: Model call event to add
        """
        self.events.append(event)

    def calculate_metrics(
        self, provider: Optional[str] = None, model_id: Optional[str] = None
    ) -> ModelMetrics:
        """Calculate aggregated metrics for the specified provider and model.

        Args:
            provider: Provider to filter by (optional)
            model_id: Model ID to filter by (optional)

        Returns:
            Aggregated metrics
        """
        # Filter events based on provider and model_id
        filtered_events = self.events
        if provider:
            filtered_events = [e for e in filtered_events if e.provider == provider]
        if model_id:
            filtered_events = [e for e in filtered_events if e.model_id == model_id]

        # Initialize metrics
        metrics = ModelMetrics()

        # Return empty metrics if no events
        if not filtered_events:
            return metrics

        # Calculate metrics
        metrics.total_calls = len(filtered_events)
        metrics.successful_calls = sum(1 for e in filtered_events if e.success)
        metrics.failed_calls = metrics.total_calls - metrics.successful_calls

        # Calculate token metrics
        input_tokens = [
            e.input_tokens for e in filtered_events if e.input_tokens is not None
        ]
        output_tokens = [
            e.output_tokens for e in filtered_events if e.output_tokens is not None
        ]

        metrics.total_input_tokens = sum(input_tokens) if input_tokens else 0
        metrics.total_output_tokens = sum(output_tokens) if output_tokens else 0
        metrics.total_tokens = metrics.total_input_tokens + metrics.total_output_tokens

        # Calculate latency metrics
        latencies = [
            e.duration_ms for e in filtered_events if e.duration_ms is not None
        ]
        if latencies:
            metrics.avg_latency_ms = sum(latencies) / len(latencies)

            # Calculate percentiles
            sorted_latencies = sorted(latencies)
            p95_index = int(len(sorted_latencies) * 0.95)
            p99_index = int(len(sorted_latencies) * 0.99)

            metrics.p95_latency_ms = (
                sorted_latencies[p95_index]
                if p95_index < len(sorted_latencies)
                else sorted_latencies[-1]
            )
            metrics.p99_latency_ms = (
                sorted_latencies[p99_index]
                if p99_index < len(sorted_latencies)
                else sorted_latencies[-1]
            )

        return metrics

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report.

        Returns:
            Dictionary containing the performance report
        """
        # Calculate overall metrics
        overall_metrics = self.calculate_metrics()

        # Calculate metrics per provider
        providers = set(event.provider for event in self.events)
        provider_metrics = {
            provider: self.calculate_metrics(provider=provider).dict()
            for provider in providers
        }

        # Calculate metrics per model
        models = set((event.provider, event.model_id) for event in self.events)
        model_metrics = {
            f"{provider}/{model_id}": self.calculate_metrics(
                provider=provider, model_id=model_id
            ).dict()
            for provider, model_id in models
        }

        return {
            "overall": overall_metrics.dict(),
            "by_provider": provider_metrics,
            "by_model": model_metrics,
            "total_events": len(self.events),
            "time_range": {
                "start": min(event.timestamp for event in self.events).isoformat()
                if self.events
                else None,
                "end": max(event.timestamp for event in self.events).isoformat()
                if self.events
                else None,
            },
        }


class PerformanceMonitor:
    """Monitors model performance in real-time.

    This class provides utilities for monitoring model performance in real-time,
    including tracking model calls and calculating metrics.
    """

    def __init__(self):
        """Initialize the performance monitor."""
        self.analyzer = PerformanceAnalyzer()
        self._current_calls: Dict[str, Dict[str, Any]] = {}

    def start_call(
        self, model_id: str, provider: str, call_type: Union[ModelCallType, str]
    ) -> str:
        """Start tracking a model call.

        Args:
            model_id: Identifier of the model
            provider: Provider of the model
            call_type: Type of model call

        Returns:
            Call ID for tracking the call
        """
        call_id = f"{time.time()}_{model_id}_{provider}"

        # Convert string to enum if needed
        if isinstance(call_type, str):
            call_type = ModelCallType(call_type)

        self._current_calls[call_id] = {
            "model_id": model_id,
            "provider": provider,
            "call_type": call_type,
            "start_time": time.time(),
            "metadata": {},
        }

        return call_id

    def end_call(
        self,
        call_id: str,
        success: bool = True,
        error: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ModelCallEvent]:
        """End tracking a model call and record the event.

        Args:
            call_id: Call ID returned by start_call
            success: Whether the call was successful
            error: Error message if the call failed
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            metadata: Additional metadata about the call

        Returns:
            The recorded model call event, or None if the call ID is invalid
        """
        if call_id not in self._current_calls:
            return None

        call_data = self._current_calls.pop(call_id)
        end_time = time.time()
        duration_ms = (end_time - call_data["start_time"]) * 1000

        # Combine metadata
        combined_metadata = call_data.get("metadata", {}).copy()
        if metadata:
            combined_metadata.update(metadata)

        # Create event
        event = ModelCallEvent(
            model_id=call_data["model_id"],
            provider=call_data["provider"],
            call_type=call_data["call_type"],
            timestamp=datetime.fromtimestamp(call_data["start_time"]),
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=success,
            error=error,
            metadata=combined_metadata,
        )

        # Add event to analyzer
        self.analyzer.add_event(event)

        return event

    def update_call_metadata(self, call_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for an ongoing call.

        Args:
            call_id: Call ID returned by start_call
            metadata: Metadata to update

        Returns:
            True if the call ID is valid and metadata was updated, False otherwise
        """
        if call_id not in self._current_calls:
            return False

        if "metadata" not in self._current_calls[call_id]:
            self._current_calls[call_id]["metadata"] = {}

        self._current_calls[call_id]["metadata"].update(metadata)
        return True

    def get_metrics(
        self, provider: Optional[str] = None, model_id: Optional[str] = None
    ) -> ModelMetrics:
        """Get current performance metrics.

        Args:
            provider: Provider to filter by (optional)
            model_id: Model ID to filter by (optional)

        Returns:
            Current performance metrics
        """
        return self.analyzer.calculate_metrics(provider=provider, model_id=model_id)

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report.

        Returns:
            Dictionary containing the performance report
        """
        return self.analyzer.generate_report()


class PerformanceReporter:
    """Reports model performance metrics.

    This class provides utilities for reporting model performance metrics
    to various destinations, such as logging, monitoring systems, or dashboards.
    """

    def __init__(self, analyzer: Optional[PerformanceAnalyzer] = None):
        """Initialize the performance reporter.

        Args:
            analyzer: Performance analyzer to use (optional)
        """
        self.analyzer = analyzer or PerformanceAnalyzer()
        self._report_handlers: List[Callable[[Dict[str, Any]], None]] = []

    def add_report_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Add a report handler.

        Args:
            handler: Function that takes a report dictionary and processes it
        """
        self._report_handlers.append(handler)

    def generate_report(self) -> Dict[str, Any]:
        """Generate a performance report.

        Returns:
            Dictionary containing the performance report
        """
        return self.analyzer.generate_report()

    def report(self) -> None:
        """Generate a report and send it to all registered handlers."""
        report = self.generate_report()
        for handler in self._report_handlers:
            try:
                handler(report)
            except Exception as e:
                # Log the error but continue with other handlers
                print(f"Error in report handler: {e}")

    def log_report(self, level: str = "info") -> None:
        """Log the performance report.

        Args:
            level: Log level to use
        """
        report = self.generate_report()
        # Simple logging implementation
        print(f"[{level.upper()}] Performance Report: {report}")


class PerformanceTracker:
    """Tracks model performance.

    This class provides a high-level interface for tracking model performance,
    combining monitoring, analysis, and reporting capabilities.
    """

    def __init__(self):
        """Initialize the performance tracker."""
        self.analyzer = PerformanceAnalyzer()
        self.monitor = PerformanceMonitor()
        self.reporter = PerformanceReporter(self.analyzer)

        # Link the monitor's analyzer to our analyzer
        self.monitor.analyzer = self.analyzer

    def track_call(
        self,
        model_id: str,
        provider: str,
        call_type: Union[ModelCallType, str],
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        duration_ms: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ModelCallEvent:
        """Track a model call.

        Args:
            model_id: Identifier of the model
            provider: Provider of the model
            call_type: Type of model call
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Duration of the call in milliseconds
            success: Whether the call was successful
            error: Error message if the call failed
            metadata: Additional metadata about the call

        Returns:
            The recorded model call event
        """
        # Convert string to enum if needed
        if isinstance(call_type, str):
            call_type = ModelCallType(call_type)

        # Create event
        event = ModelCallEvent(
            model_id=model_id,
            provider=provider,
            call_type=call_type,
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=success,
            error=error,
            metadata=metadata or {},
        )

        # Add event to analyzer
        self.analyzer.add_event(event)

        return event

    def start_call(
        self, model_id: str, provider: str, call_type: Union[ModelCallType, str]
    ) -> str:
        """Start tracking a model call.

        Args:
            model_id: Identifier of the model
            provider: Provider of the model
            call_type: Type of model call

        Returns:
            Call ID for tracking the call
        """
        return self.monitor.start_call(model_id, provider, call_type)

    def end_call(
        self,
        call_id: str,
        success: bool = True,
        error: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ModelCallEvent]:
        """End tracking a model call.

        Args:
            call_id: Call ID returned by start_call
            success: Whether the call was successful
            error: Error message if the call failed
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            metadata: Additional metadata about the call

        Returns:
            The recorded model call event, or None if the call ID is invalid
        """
        return self.monitor.end_call(
            call_id, success, error, input_tokens, output_tokens, metadata
        )

    def get_metrics(
        self, provider: Optional[str] = None, model_id: Optional[str] = None
    ) -> ModelMetrics:
        """Get current performance metrics.

        Args:
            provider: Provider to filter by (optional)
            model_id: Model ID to filter by (optional)

        Returns:
            Current performance metrics
        """
        return self.analyzer.calculate_metrics(provider=provider, model_id=model_id)

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report.

        Returns:
            Dictionary containing the performance report
        """
        return self.analyzer.generate_report()

    def report(self) -> None:
        """Generate a report and send it to all registered handlers."""
        self.reporter.report()

    def add_report_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Add a report handler.

        Args:
            handler: Function that takes a report dictionary and processes it
        """
        self.reporter.add_report_handler(handler)
