"""Metrics collection and monitoring system."""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime
import threading
import logging
from collections import defaultdict

@dataclass
class Metric:
    """Base class for metric types."""
    name: str
    labels: Dict[str, str]
    timestamp: datetime

@dataclass
class Counter(Metric):
    """Counter metric type for counting events."""
    value: int = 0

    def inc(self, amount: int = 1) -> None:
        """Increment the counter.
        
        Args:
            amount: Amount to increment by (default: 1)
        """
        self.value += amount

@dataclass
class Gauge(Metric):
    """Gauge metric type for variable measurements."""
    value: float = 0.0

    def set(self, value: float) -> None:
        """Set the gauge value.
        
        Args:
            value: New value to set
        """
        self.value = value

    def inc(self, amount: float = 1.0) -> None:
        """Increment the gauge.
        
        Args:
            amount: Amount to increment by (default: 1.0)
        """
        self.value += amount

    def dec(self, amount: float = 1.0) -> None:
        """Decrement the gauge.
        
        Args:
            amount: Amount to decrement by (default: 1.0)
        """
        self.value -= amount

@dataclass
class Histogram(Metric):
    """Histogram metric type for measuring distributions."""
    buckets: List[float]
    values: List[float]
    sum: float = 0.0
    count: int = 0

    def observe(self, value: float) -> None:
        """Record an observation.
        
        Args:
            value: Value to record
        """
        self.values.append(value)
        self.sum += value
        self.count += 1

class MetricsCollector:
    """Collector for system metrics.
    
    This class provides a centralized way to collect and manage various
    types of metrics throughout the system.
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._metrics: Dict[str, Dict[str, Metric]] = defaultdict(dict)
        self._lock = threading.Lock()
        self._logger = logging.getLogger(__name__)

    def counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Counter:
        """Get or create a counter metric.
        
        Args:
            name: Metric name
            labels: Optional metric labels
            
        Returns:
            Counter metric instance
        """
        return self._get_or_create_metric(Counter, name, labels or {})

    def gauge(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Gauge:
        """Get or create a gauge metric.
        
        Args:
            name: Metric name
            labels: Optional metric labels
            
        Returns:
            Gauge metric instance
        """
        return self._get_or_create_metric(Gauge, name, labels or {})

    def histogram(
        self,
        name: str,
        buckets: List[float],
        labels: Optional[Dict[str, str]] = None
    ) -> Histogram:
        """Get or create a histogram metric.
        
        Args:
            name: Metric name
            buckets: Histogram buckets
            labels: Optional metric labels
            
        Returns:
            Histogram metric instance
        """
        return self._get_or_create_metric(
            Histogram,
            name,
            labels or {},
            buckets=buckets,
            values=[]
        )

    def _get_or_create_metric(
        self,
        metric_type: type,
        name: str,
        labels: Dict[str, str],
        **kwargs: Any
    ) -> Union[Counter, Gauge, Histogram]:
        """Get an existing metric or create a new one.
        
        Args:
            metric_type: Type of metric to create
            name: Metric name
            labels: Metric labels
            **kwargs: Additional arguments for metric creation
            
        Returns:
            Metric instance
        """
        key = self._get_metric_key(name, labels)
        
        with self._lock:
            if key not in self._metrics[name]:
                self._metrics[name][key] = metric_type(
                    name=name,
                    labels=labels,
                    timestamp=datetime.now(),
                    **kwargs
                )
            
            return self._metrics[name][key]

    def _get_metric_key(self, name: str, labels: Dict[str, str]) -> str:
        """Generate a unique key for a metric.
        
        Args:
            name: Metric name
            labels: Metric labels
            
        Returns:
            Unique metric key
        """
        sorted_labels = sorted(labels.items())
        labels_str = ",".join(f"{k}={v}" for k, v in sorted_labels)
        return f"{name}:{labels_str}"

    def get_metrics(self) -> Dict[str, Dict[str, Metric]]:
        """Get all collected metrics.
        
        Returns:
            Dictionary of all metrics
        """
        with self._lock:
            return dict(self._metrics)

    def clear(self) -> None:
        """Clear all collected metrics."""
        with self._lock:
            self._metrics.clear()
            self._logger.info("Cleared all metrics")
