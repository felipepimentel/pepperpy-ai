"""Metrics manager module.

This module provides the metrics manager for centralized metrics management.
"""

from typing import Dict, List, Optional, Union

from pepperpy.core.metrics.types import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    MetricType,
    MetricValue,
    MetricLabels,
)


class MetricsManager:
    """Manager for metrics collection and monitoring.
    
    This class provides centralized management of metrics, including:
    - Creation and retrieval of metrics
    - Type-safe access to metrics
    - Support for labels and metadata
    
    Example:
        >>> manager = MetricsManager()
        >>> counter = manager.counter("requests", "Total requests")
        >>> counter.inc()  # Increment counter
        >>> counter.get()  # Get current value
        1.0
    """

    def __init__(self) -> None:
        """Initialize metrics manager."""
        self._metrics: Dict[str, Union[Counter, Gauge, Histogram, Summary]] = {}

    def counter(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
    ) -> Counter:
        """Create or get a counter metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional list of label names
            
        Returns:
            Counter metric instance
        """
        if name not in self._metrics:
            self._metrics[name] = Counter(name, description, labels)
        metric = self._metrics[name]
        if not isinstance(metric, Counter):
            raise TypeError(f"Metric {name} is not a counter")
        return metric

    def gauge(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
    ) -> Gauge:
        """Create or get a gauge metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional list of label names
            
        Returns:
            Gauge metric instance
        """
        if name not in self._metrics:
            self._metrics[name] = Gauge(name, description, labels)
        metric = self._metrics[name]
        if not isinstance(metric, Gauge):
            raise TypeError(f"Metric {name} is not a gauge")
        return metric

    def histogram(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None,
        labels: Optional[List[str]] = None,
    ) -> Histogram:
        """Create or get a histogram metric.
        
        Args:
            name: Metric name
            description: Metric description
            buckets: Optional bucket boundaries
            labels: Optional list of label names
            
        Returns:
            Histogram metric instance
        """
        if name not in self._metrics:
            self._metrics[name] = Histogram(name, description, buckets, labels)
        metric = self._metrics[name]
        if not isinstance(metric, Histogram):
            raise TypeError(f"Metric {name} is not a histogram")
        return metric

    def summary(
        self,
        name: str,
        description: str,
        quantiles: Optional[List[float]] = None,
        labels: Optional[List[str]] = None,
    ) -> Summary:
        """Create or get a summary metric.
        
        Args:
            name: Metric name
            description: Metric description
            quantiles: Optional quantiles to track
            labels: Optional list of label names
            
        Returns:
            Summary metric instance
        """
        if name not in self._metrics:
            self._metrics[name] = Summary(name, description, quantiles, labels)
        metric = self._metrics[name]
        if not isinstance(metric, Summary):
            raise TypeError(f"Metric {name} is not a summary")
        return metric

    def get_metric(
        self, name: str
    ) -> Union[Counter, Gauge, Histogram, Summary]:
        """Get a metric by name.
        
        Args:
            name: Metric name
            
        Returns:
            Metric instance
            
        Raises:
            KeyError: If metric not found
        """
        if name not in self._metrics:
            raise KeyError(f"Metric {name} not found")
        return self._metrics[name]

    def get_all_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram, Summary]]:
        """Get all registered metrics.
        
        Returns:
            Dictionary mapping metric names to instances
        """
        return self._metrics.copy()


__all__ = ["MetricsManager"]
