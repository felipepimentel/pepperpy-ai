# Metrics and Monitoring

PepperPy AI includes comprehensive metrics and monitoring capabilities to track performance, usage, and costs.

## Overview

The metrics system provides:
- Performance monitoring
- Usage tracking
- Cost analysis
- Error reporting
- System health checks

## Available Metrics

### Performance Metrics
- Response time
- Token usage
- Request latency
- Cache hit rate
- Error rate

### Usage Metrics
- API calls per provider
- Token consumption
- Request volume
- Active agents
- Cache utilization

### Cost Metrics
- API costs per provider
- Token costs
- Total usage costs
- Cost per request
- Cost optimization metrics

## Using Metrics

### Basic Usage

```python
from pepperpy_ai.metrics import MetricsCollector
from pepperpy_ai.config import Config

async def metrics_example():
    config = Config()
    metrics = MetricsCollector(config)
    
    # Record API call
    async with metrics.record_call("openai"):
        # Your API call here
        pass
    
    # Get metrics
    stats = await metrics.get_stats()
    print(stats)
```

### Custom Metrics

```python
from pepperpy_ai.metrics import MetricsCollector, Metric

async def custom_metrics_example():
    metrics = MetricsCollector()
    
    # Define custom metric
    custom_metric = Metric(
        name="custom_operation",
        description="Custom operation metric",
        unit="operations"
    )
    
    # Record custom metric
    metrics.record_metric(custom_metric, 1.0)
```

## Monitoring Configuration

Configure monitoring settings:

```python
from pepperpy_ai.config import Config

config = Config(
    metrics_enabled=True,
    metrics_interval=60,  # seconds
    metrics_export="prometheus"
)
```

## Advanced Features

### Prometheus Integration

```python
from pepperpy_ai.metrics import PrometheusExporter

async def prometheus_example():
    exporter = PrometheusExporter()
    
    # Export metrics
    metrics_data = await exporter.export()
    
    # Start metrics server
    await exporter.start_server(port=8000)
```

### Cost Analysis

```python
from pepperpy_ai.metrics import CostAnalyzer

async def cost_analysis_example():
    analyzer = CostAnalyzer()
    
    # Get cost report
    report = await analyzer.get_cost_report()
    
    print("Total cost:", report.total_cost)
    print("Cost by provider:", report.cost_by_provider)
    print("Cost by operation:", report.cost_by_operation)
```

## Best Practices

1. **Metric Collection**
   - Collect relevant metrics only
   - Use appropriate metric types
   - Set meaningful thresholds

2. **Performance Impact**
   - Minimize metric overhead
   - Use sampling when appropriate
   - Batch metric updates

3. **Storage**
   - Configure appropriate retention
   - Use efficient storage backends
   - Implement data aggregation

4. **Monitoring**
   - Set up alerts
   - Monitor trends
   - Track anomalies

## Environment Variables

Configure metrics settings:

```bash
PEPPERPY_METRICS_ENABLED=true
PEPPERPY_METRICS_INTERVAL=60
PEPPERPY_METRICS_EXPORT=prometheus
PEPPERPY_METRICS_PORT=8000
```

## Examples

### Performance Monitoring

```python
from pepperpy_ai.metrics import PerformanceMonitor

async def performance_example():
    monitor = PerformanceMonitor()
    
    async with monitor.measure("operation"):
        # Operation to measure
        await some_operation()
    
    stats = await monitor.get_stats()
    print("Average response time:", stats.avg_response_time)
    print("95th percentile:", stats.p95_response_time)
```

### Usage Tracking

```python
from pepperpy_ai.metrics import UsageTracker

async def usage_example():
    tracker = UsageTracker()
    
    # Track API usage
    await tracker.track_api_call(
        provider="openai",
        operation="completion",
        tokens=100
    )
    
    # Get usage report
    usage = await tracker.get_usage_report()
    print("Total API calls:", usage.total_calls)
    print("Total tokens:", usage.total_tokens)
```

### Health Checks

```python
from pepperpy_ai.metrics import HealthChecker

async def health_check_example():
    checker = HealthChecker()
    
    # Run health check
    status = await checker.check_health()
    
    if status.is_healthy:
        print("System is healthy")
    else:
        print("Issues found:", status.issues)
``` 