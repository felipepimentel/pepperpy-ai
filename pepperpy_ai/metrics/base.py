"""Base metrics module."""

from abc import ABC, abstractmethod
from typing import TypedDict

from ..ai_types import Message


class MetricParams(TypedDict, total=False):
    """Parameters for metric calculation."""

    window_size: int
    threshold: float
    weights: dict[str, float]


class BaseMetric(ABC):
    """Base class for metrics."""

    @abstractmethod
    async def calculate(self, messages: list[Message], **kwargs: MetricParams) -> float:
        """Calculate metric value.

        Args:
            messages: List of messages to calculate metric for.
            **kwargs: Additional metric parameters.

        Returns:
            float: Calculated metric value.
        """
        pass
