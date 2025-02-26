"""Module for evaluating agent performance using various metrics."""
from typing import List, Optional, Dict, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum
import statistics


class MetricType(Enum):
    """Types of evaluation metrics."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    COST_EFFICIENCY = "cost_efficiency"
    CUSTOM = "custom"


@dataclass
class MetricResult:
    """Result of a metric evaluation."""
    type: MetricType
    value: float
    confidence: Optional[float] = None
    metadata: Optional[dict] = None


@dataclass
class EvaluationResult:
    """Combined results from multiple metrics."""
    metrics: Dict[str, MetricResult]
    aggregate_score: float
    metadata: Optional[dict] = None


class BaseMetric:
    """Base class for evaluation metrics."""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight

    def compute(self, data: Dict[str, Any]) -> MetricResult:
        """Compute the metric value."""
        raise NotImplementedError


class AccuracyMetric(BaseMetric):
    """Measures prediction accuracy."""
    
    def compute(self, data: Dict[str, Any]) -> MetricResult:
        """Compute accuracy from predictions and ground truth."""
        predictions = data.get('predictions', [])
        ground_truth = data.get('ground_truth', [])
        
        if len(predictions) != len(ground_truth):
            raise ValueError("Predictions and ground truth must have same length")
        
        if not predictions:
            raise ValueError("No data to evaluate")
        
        correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
        accuracy = correct / len(predictions)
        
        return MetricResult(
            type=MetricType.ACCURACY,
            value=accuracy
        )


class PrecisionRecallMetric(BaseMetric):
    """Measures precision and recall."""
    
    def compute(self, data: Dict[str, Any]) -> MetricResult:
        """Compute precision or recall."""
        predictions = data.get('predictions', [])
        ground_truth = data.get('ground_truth', [])
        
        if len(predictions) != len(ground_truth):
            raise ValueError("Predictions and ground truth must have same length")
        
        if not predictions:
            raise ValueError("No data to evaluate")
        
        true_positives = sum(1 for p, g in zip(predictions, ground_truth) if p and g)
        false_positives = sum(1 for p, g in zip(predictions, ground_truth) if p and not g)
        false_negatives = sum(1 for p, g in zip(predictions, ground_truth) if not p and g)
        
        if self.name == "precision":
            denominator = true_positives + false_positives
            value = true_positives / denominator if denominator > 0 else 0
            metric_type = MetricType.PRECISION
        else:  # recall
            denominator = true_positives + false_negatives
            value = true_positives / denominator if denominator > 0 else 0
            metric_type = MetricType.RECALL
        
        return MetricResult(
            type=metric_type,
            value=value
        )


class LatencyMetric(BaseMetric):
    """Measures response time performance."""
    
    def compute(self, data: Dict[str, Any]) -> MetricResult:
        """Compute latency statistics."""
        latencies = data.get('latencies', [])
        
        if not latencies:
            raise ValueError("No latency data to evaluate")
        
        avg_latency = statistics.mean(latencies)
        
        return MetricResult(
            type=MetricType.LATENCY,
            value=avg_latency,
            metadata={
                'p50': statistics.median(latencies),
                'p90': sorted(latencies)[int(len(latencies) * 0.9)],
                'p99': sorted(latencies)[int(len(latencies) * 0.99)]
            }
        )


class CostEfficiencyMetric(BaseMetric):
    """Measures cost efficiency of operations."""
    
    def compute(self, data: Dict[str, Any]) -> MetricResult:
        """Compute cost efficiency metrics."""
        costs = data.get('costs', [])
        outcomes = data.get('outcomes', [])
        
        if not costs or not outcomes:
            raise ValueError("Missing cost or outcome data")
        
        if len(costs) != len(outcomes):
            raise ValueError("Costs and outcomes must have same length")
        
        # Calculate cost per successful outcome
        successful_costs = [c for c, o in zip(costs, outcomes) if o]
        if not successful_costs:
            return MetricResult(
                type=MetricType.COST_EFFICIENCY,
                value=0.0
            )
        
        avg_cost_per_success = statistics.mean(successful_costs)
        
        return MetricResult(
            type=MetricType.COST_EFFICIENCY,
            value=1.0 / avg_cost_per_success,  # Higher value means better efficiency
            metadata={
                'avg_cost_per_success': avg_cost_per_success,
                'total_cost': sum(costs),
                'success_rate': sum(1 for o in outcomes if o) / len(outcomes)
            }
        )


class CustomMetric(BaseMetric):
    """User-defined custom metric."""
    
    def __init__(self, name: str, compute_fn: Callable[[Dict[str, Any]], float], weight: float = 1.0):
        super().__init__(name, weight)
        self.compute_fn = compute_fn

    def compute(self, data: Dict[str, Any]) -> MetricResult:
        """Compute custom metric using provided function."""
        try:
            value = self.compute_fn(data)
            return MetricResult(
                type=MetricType.CUSTOM,
                value=value
            )
        except Exception as e:
            raise ValueError(f"Error computing custom metric: {str(e)}")


class MetricAggregator:
    """Aggregates multiple metrics into a single score."""
    
    def __init__(self, metrics: List[BaseMetric]):
        self.metrics = metrics
        self._normalize_weights()

    def _normalize_weights(self):
        """Normalize metric weights to sum to 1."""
        total_weight = sum(m.weight for m in self.metrics)
        if total_weight > 0:
            for metric in self.metrics:
                metric.weight /= total_weight

    def evaluate(self, data: Dict[str, Any]) -> EvaluationResult:
        """Compute all metrics and aggregate results."""
        results = {}
        weighted_sum = 0.0
        
        for metric in self.metrics:
            try:
                result = metric.compute(data)
                results[metric.name] = result
                weighted_sum += result.value * metric.weight
            except ValueError as e:
                print(f"Warning: Could not compute metric {metric.name}: {str(e)}")
        
        return EvaluationResult(
            metrics=results,
            aggregate_score=weighted_sum
        ) 