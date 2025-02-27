"""Sistema de métricas para monitoramento.

Implementa o sistema de métricas para monitoramento de componentes,
fornecendo contadores, histogramas e medidores.
"""

from typing import Dict, List, Optional


class MetricsManager:
    """Manager for component metrics."""

    def __init__(self) -> None:
        """Initialize metrics manager."""
        self._counters: Dict[str, Counter] = {}
        self._histograms: Dict[str, Histogram] = {}

    def create_counter(self, name: str, description: str = "") -> "Counter":
        """Create a new counter.

        Args:
            name: Counter name
            description: Counter description

        Returns:
            New counter instance
        """
        counter = Counter(name, description)
        self._counters[name] = counter
        return counter

    def create_histogram(
        self, name: str, buckets: List[float], description: str = ""
    ) -> "Histogram":
        """Create a new histogram.

        Args:
            name: Histogram name
            buckets: Histogram buckets
            description: Histogram description

        Returns:
            New histogram instance
        """
        histogram = Histogram(name, buckets, description)
        self._histograms[name] = histogram
        return histogram

    def get_counter(self, name: str) -> Optional["Counter"]:
        """Get counter by name.

        Args:
            name: Counter name

        Returns:
            Counter if found, None otherwise
        """
        return self._counters.get(name)

    def get_histogram(self, name: str) -> Optional["Histogram"]:
        """Get histogram by name.

        Args:
            name: Histogram name

        Returns:
            Histogram if found, None otherwise
        """
        return self._histograms.get(name)


class Counter:
    """Simple counter metric."""

    def __init__(self, name: str, description: str = "") -> None:
        """Initialize counter.

        Args:
            name: Counter name
            description: Counter description
        """
        self.name = name
        self.description = description
        self._value = 0

    def increment(self, value: int = 1) -> None:
        """Increment counter.

        Args:
            value: Value to increment by
        """
        self._value += value

    @property
    def value(self) -> int:
        """Get current value.

        Returns:
            Current counter value
        """
        return self._value


class Histogram:
    """Histogram metric with buckets."""

    def __init__(self, name: str, buckets: List[float], description: str = "") -> None:
        """Initialize histogram.

        Args:
            name: Histogram name
            buckets: Histogram buckets
            description: Histogram description
        """
        self.name = name
        self.description = description
        self.buckets = sorted(buckets)
        self._counts = {b: 0 for b in buckets}
        self._sum = 0.0
        self._count = 0

    def observe(self, value: float) -> None:
        """Record an observation.

        Args:
            value: Value to record
        """
        self._sum += value
        self._count += 1
        for bucket in self.buckets:
            if value <= bucket:
                self._counts[bucket] += 1

    @property
    def counts(self) -> Dict[float, int]:
        """Get bucket counts.

        Returns:
            Dictionary mapping buckets to counts
        """
        return self._counts.copy()

    @property
    def sum(self) -> float:
        """Get sum of observations.

        Returns:
            Sum of all observations
        """
        return self._sum

    @property
    def count(self) -> int:
        """Get total number of observations.

        Returns:
            Total number of observations
        """
        return self._count
