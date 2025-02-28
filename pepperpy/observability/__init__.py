"""Observability package for PepperPy.

This package provides comprehensive observability features including:
- Health monitoring
- Cost tracking
- Hallucination detection
- Model performance monitoring
- Metrics collection
- Distributed tracing
- System monitoring
"""

from .health import (
    HealthCheck,
    HealthChecker,
    HealthCheckResult,
    HealthStatus,
    SystemHealthCheck,
)
from .metrics.collector import (
    Metric,
    MetricsCollector,
    MetricType,
)
from .metrics.manager import MetricsRegistry
from .metrics.model_performance import (
    ModelCallEvent,
    ModelMetrics,
    PerformanceAnalyzer,
    PerformanceMonitor,
    PerformanceReporter,
    PerformanceTracker,
)
from .migration import MigrationHelper
from .monitoring.cost_tracking import (
    BudgetAlert,
    CostEvent,
    CostMonitor,
    CostOptimizer,
    CostTracker,
)
from .monitoring.hallucination_detection import (
    BaseHallucinationDetector,
    HallucinationDetection,
    HallucinationDetector,
    HallucinationEvent,
    HallucinationMonitor,
    HallucinationType,
)
from .monitoring.runtime import (
    RuntimeMetrics,
    RuntimeMonitor,
)
from .monitoring.system import (
    SystemMetrics,
    SystemMonitor,
)

__all__ = [
    # Health monitoring
    "HealthStatus",
    "HealthCheckResult",
    "HealthCheck",
    "HealthChecker",
    "SystemHealthCheck",
    # Metrics
    "MetricType",
    "Metric",
    "MetricsCollector",
    "MetricsRegistry",
    # Model Performance
    "ModelCallEvent",
    "ModelMetrics",
    "PerformanceTracker",
    "PerformanceAnalyzer",
    "PerformanceMonitor",
    "PerformanceReporter",
    # Monitoring
    "RuntimeMetrics",
    "RuntimeMonitor",
    "SystemMetrics",
    "SystemMonitor",
    # Cost Tracking
    "CostEvent",
    "CostTracker",
    "BudgetAlert",
    "CostMonitor",
    "CostOptimizer",
    # Hallucination Detection
    "HallucinationType",
    "HallucinationEvent",
    "HallucinationDetection",
    "BaseHallucinationDetector",
    "HallucinationDetector",
    "HallucinationMonitor",
    # Migration
    "MigrationHelper",
]
