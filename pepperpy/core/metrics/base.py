"""Core metrics interfaces and base classes."""

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

MetricValue = Union[int, float, str, bool]
MetricLabels = Dict[str, str]


class MetricConfig(BaseModel):
    name: str
    description: str
    unit: str = "count"
    labels: MetricLabels = Field(default_factory=dict)


class MetricPoint(BaseModel):
    name: str
    value: MetricValue
    timestamp: float
    labels: MetricLabels = Field(default_factory=dict)


class BaseMetric(ABC):
    def __init__(self, config: MetricConfig) -> None:
        self.name = config.name
        self.description = config.description
        self.unit = config.unit
        self.labels = config.labels

    @abstractmethod
    def record(self, value: MetricValue) -> None:
        pass

    @abstractmethod
    def get_points(self) -> List[MetricPoint]:
        pass


class Counter(BaseMetric):
    def __init__(self, config: MetricConfig) -> None:
        super().__init__(config)
        self._value: int = 0
        self._points: List[MetricPoint] = []

    def record(self, value: MetricValue = 1) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("Counter value must be numeric")
        if value < 0:
            raise ValueError("Counter value must be non-negative")

        self._value += int(value)
        self._points.append(
            MetricPoint(
                name=self.name,
                value=self._value,
                timestamp=time.time(),
                labels=self.labels,
            )
        )

    def get_points(self) -> List[MetricPoint]:
        return self._points.copy()


class Gauge(BaseMetric):
    def __init__(self, config: MetricConfig) -> None:
        super().__init__(config)
        self._value: Optional[float] = None
        self._points: List[MetricPoint] = []

    def record(self, value: MetricValue) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("Gauge value must be numeric")

        self._value = float(value)
        self._points.append(
            MetricPoint(
                name=self.name,
                value=self._value,
                timestamp=time.time(),
                labels=self.labels,
            )
        )

    def get_points(self) -> List[MetricPoint]:
        return self._points.copy()
