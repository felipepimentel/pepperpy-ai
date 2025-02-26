"""Module for tracking and analyzing AI model performance metrics."""
from typing import Dict, Optional, List, Any, Union
from dataclasses import dataclass
from datetime import datetime
import statistics
import json


@dataclass
class ModelCall:
    """Represents a single model API call."""
    timestamp: datetime
    model_id: str
    operation: str
    input_tokens: int
    output_tokens: int
    duration_ms: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[dict] = None


@dataclass
class ModelMetrics:
    """Aggregated metrics for model performance."""
    total_calls: int
    success_rate: float
    avg_latency: float
    p50_latency: float
    p90_latency: float
    p99_latency: float
    avg_input_tokens: float
    avg_output_tokens: float
    error_distribution: Dict[str, int]
    metadata: Optional[dict] = None


class PerformanceTracker:
    """Tracks model performance metrics."""
    
    def __init__(self):
        self.calls: Dict[str, List[ModelCall]] = {}  # model_id -> calls

    def record_call(self, call: ModelCall):
        """Record a model call."""
        if call.model_id not in self.calls:
            self.calls[call.model_id] = []
        self.calls[call.model_id].append(call)

    def get_metrics(self,
                   model_id: str,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> ModelMetrics:
        """Calculate metrics for a model within a time range."""
        if model_id not in self.calls:
            raise ValueError(f"No data for model {model_id}")
        
        # Filter calls by time range
        calls = self.calls[model_id]
        if start_time:
            calls = [c for c in calls if c.timestamp >= start_time]
        if end_time:
            calls = [c for c in calls if c.timestamp <= end_time]
        
        if not calls:
            raise ValueError("No data in specified time range")
        
        # Calculate metrics
        total_calls = len(calls)
        success_calls = [c for c in calls if c.success]
        success_rate = len(success_calls) / total_calls
        
        latencies = [c.duration_ms for c in calls]
        latencies.sort()
        
        error_dist = {}
        for call in calls:
            if not call.success and call.error:
                error_dist[call.error] = error_dist.get(call.error, 0) + 1
        
        return ModelMetrics(
            total_calls=total_calls,
            success_rate=success_rate,
            avg_latency=statistics.mean(latencies),
            p50_latency=statistics.median(latencies),
            p90_latency=latencies[int(total_calls * 0.9)],
            p99_latency=latencies[int(total_calls * 0.99)],
            avg_input_tokens=statistics.mean(c.input_tokens for c in calls),
            avg_output_tokens=statistics.mean(c.output_tokens for c in calls),
            error_distribution=error_dist
        )


class PerformanceAnalyzer:
    """Analyzes model performance patterns and trends."""
    
    def __init__(self, tracker: PerformanceTracker):
        self.tracker = tracker

    def analyze_trends(self,
                      model_id: str,
                      window_size: str = '1h') -> Dict[str, Any]:
        """Analyze performance trends over time."""
        # Implementation would analyze metrics over time windows
        raise NotImplementedError

    def detect_anomalies(self,
                        model_id: str,
                        threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalous performance patterns."""
        # Implementation would use statistical methods to detect anomalies
        raise NotImplementedError

    def compare_models(self,
                      model_ids: List[str],
                      metrics: List[str]) -> Dict[str, Dict[str, float]]:
        """Compare performance across different models."""
        results = {}
        
        for model_id in model_ids:
            try:
                model_metrics = self.tracker.get_metrics(model_id)
                results[model_id] = {
                    'success_rate': model_metrics.success_rate,
                    'avg_latency': model_metrics.avg_latency,
                    'p90_latency': model_metrics.p90_latency,
                    'avg_input_tokens': model_metrics.avg_input_tokens,
                    'avg_output_tokens': model_metrics.avg_output_tokens
                }
            except ValueError:
                continue
        
        return results


class PerformanceMonitor:
    """High-level interface for model performance monitoring."""
    
    def __init__(self,
                 tracker: PerformanceTracker,
                 analyzer: PerformanceAnalyzer):
        self.tracker = tracker
        self.analyzer = analyzer
        self.alerts: Dict[str, Dict[str, float]] = {}  # model_id -> metric thresholds

    def set_alert_threshold(self,
                          model_id: str,
                          metric: str,
                          threshold: float):
        """Set an alert threshold for a metric."""
        if model_id not in self.alerts:
            self.alerts[model_id] = {}
        self.alerts[model_id][metric] = threshold

    def check_thresholds(self) -> List[Dict[str, Any]]:
        """Check if any metrics exceed their thresholds."""
        alerts = []
        
        for model_id, thresholds in self.alerts.items():
            try:
                metrics = self.tracker.get_metrics(model_id)
                
                for metric, threshold in thresholds.items():
                    current_value = getattr(metrics, metric, None)
                    if current_value is not None and current_value > threshold:
                        alerts.append({
                            'model_id': model_id,
                            'metric': metric,
                            'threshold': threshold,
                            'current_value': current_value,
                            'timestamp': datetime.now().isoformat()
                        })
            except ValueError:
                continue
        
        return alerts

    def generate_report(self,
                       model_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        if not model_ids:
            model_ids = list(self.tracker.calls.keys())
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'models': {}
        }
        
        for model_id in model_ids:
            try:
                metrics = self.tracker.get_metrics(model_id)
                report['models'][model_id] = {
                    'metrics': {
                        'total_calls': metrics.total_calls,
                        'success_rate': metrics.success_rate,
                        'avg_latency': metrics.avg_latency,
                        'p90_latency': metrics.p90_latency,
                        'avg_tokens': {
                            'input': metrics.avg_input_tokens,
                            'output': metrics.avg_output_tokens
                        }
                    },
                    'errors': metrics.error_distribution
                }
            except ValueError:
                continue
        
        return report 