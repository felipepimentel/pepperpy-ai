"""Metrics for evaluating reasoning performance.

This module provides metrics for evaluating the performance and quality
of reasoning processes, including accuracy, consistency, and efficiency.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pepperpy.common.errors import PepperpyError


class MetricsError(PepperpyError):
    """Metrics error."""
    pass


@dataclass
class ReasoningMetrics:
    """Reasoning metrics data."""
    
    accuracy: float = 0.0
    consistency: float = 0.0
    efficiency: float = 0.0
    step_count: int = 0
    completion_time: float = 0.0
    error_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector(ABC):
    """Base class for metrics collectors."""
    
    def __init__(self, name: str):
        """Initialize collector.
        
        Args:
            name: Collector name
        """
        self.name = name
        self._metrics: List[ReasoningMetrics] = []
        
    @property
    def metrics(self) -> List[ReasoningMetrics]:
        """Get collected metrics."""
        return self._metrics
        
    @abstractmethod
    async def collect(self, **kwargs: Any) -> ReasoningMetrics:
        """Collect metrics.
        
        Args:
            **kwargs: Collection-specific arguments
            
        Returns:
            Collected metrics
            
        Raises:
            MetricsError: If collection fails
        """
        pass
        
    def validate(self) -> None:
        """Validate collector state."""
        if not self.name:
            raise ValueError("Collector name cannot be empty")
