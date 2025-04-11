from prometheus_client import Counter, Histogram, Gauge, start_http_server
from typing import Dict, Optional
import logging

class MetricsCollector:
    def __init__(self, port: int = 9090):
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # Request metrics
        self.request_counter = Counter(
            'ai_gateway_requests_total',
            'Total number of requests processed',
            ['endpoint', 'status']
        )
        
        self.request_latency = Histogram(
            'ai_gateway_request_duration_seconds',
            'Request latency in seconds',
            ['endpoint'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf'))
        )
        
        # Feature usage metrics
        self.feature_usage = Counter(
            'ai_gateway_feature_usage_total',
            'Number of times each feature is used',
            ['feature_name']
        )
        
        # System metrics
        self.system_status = Gauge(
            'ai_gateway_system_status',
            'System operational status (1=up, 0=down)'
        )
        
        self.model_latency = Histogram(
            'ai_gateway_model_latency_seconds', 
            'Model inference latency in seconds',
            ['model_name'],
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, float('inf'))
        )
        
        # Token usage metrics
        self.token_usage = Counter(
            'ai_gateway_token_usage_total',
            'Total number of tokens used',
            ['model_name', 'token_type']  # prompt or completion
        )
        
        # Error metrics
        self.error_counter = Counter(
            'ai_gateway_errors_total',
            'Total number of errors',
            ['error_type']
        )

    def start(self) -> None:
        """Start the metrics HTTP server"""
        try:
            start_http_server(self.port)
            self.logger.info(f"Started metrics server on port {self.port}")
            self.system_status.set(1)  # System is up
        except Exception as e:
            self.logger.error(f"Failed to start metrics server: {str(e)}")
            self.system_status.set(0)  # System is down
            raise

    def record_request(self, endpoint: str, status: str, duration: float) -> None:
        """Record a request and its duration"""
        self.request_counter.labels(endpoint=endpoint, status=status).inc()
        self.request_latency.labels(endpoint=endpoint).observe(duration)

    def record_feature_usage(self, feature_name: str) -> None:
        """Record usage of a feature"""
        self.feature_usage.labels(feature_name=feature_name).inc()

    def record_model_latency(self, model_name: str, duration: float) -> None:
        """Record model inference latency"""
        self.model_latency.labels(model_name=model_name).observe(duration)

    def record_token_usage(self, model_name: str, token_type: str, count: int) -> None:
        """Record token usage"""
        self.token_usage.labels(
            model_name=model_name, 
            token_type=token_type
        ).inc(count)

    def record_error(self, error_type: str) -> None:
        """Record an error"""
        self.error_counter.labels(error_type=error_type).inc()
        
    def set_system_status(self, is_up: bool) -> None:
        """Set system operational status"""
        self.system_status.set(1 if is_up else 0) 