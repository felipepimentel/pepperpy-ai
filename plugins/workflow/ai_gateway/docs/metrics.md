# AI Gateway Metrics & Trend Analysis

## Overview

The AI Gateway metrics system provides comprehensive monitoring, trend analysis, and anomaly detection capabilities. It tracks:

- Performance metrics (latency, errors, throughput)
- Feature usage metrics (DAU, WAU, MAU)
- Market trends and competitive analysis
- Seasonal patterns and anomalies

## Components

### 1. Metrics Validator

Core metrics collection and validation:

```python
from pepperpy.workflow.ai_gateway.validation import MetricsValidator, MetricsWindow

# Configure metrics window
window = MetricsWindow(
    window_size=timedelta(minutes=5),
    max_requests=1000,
    max_errors=50,
    max_latency_ms=5000
)

# Create validator
validator = MetricsValidator(window)

# Record metrics
validator.record_request(
    endpoint="/api/chat",
    duration_ms=150,
    status="success"
)

# Validate metrics
result = validator.validate_metrics()
if not result.is_valid:
    print("Issues found:", result.issues)
```

### 2. Trend Analysis

Pattern detection and forecasting:

```python
# Get trend analysis
trends = validator.get_trend_analysis()

# Check specific endpoint trends
chat_trends = trends["/api/chat"]
print("Latency trend:", chat_trends["latency"]["trend"])
print("Error trend:", chat_trends["errors"]["trend"])

# Check seasonality
pattern = chat_trends["latency"]["seasonality"]
if pattern["has_seasonality"]:
    print("Peak hour:", pattern["peak_hour"])
```

### 3. Feature Metrics

Track feature adoption and usage:

```python
validator.record_feature_metric(
    feature_id="rag",
    daily_active_users=1000,
    weekly_active_users=5000,
    monthly_active_users=20000,
    retention_rate=0.85,
    nps_score=8.5
)
```

## Configuration

### MetricsWindow Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| window_size | Time window for metrics | 5 minutes |
| max_requests | Max requests per window | 1000 |
| max_errors | Max errors per window | 50 |
| max_latency_ms | Max latency threshold | 5000 |
| error_rate_threshold | Max error rate | 0.05 |

### TrendConfig Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| min_data_points | Min points for analysis | 30 |
| forecast_window | Forecast duration | 7 days |
| seasonality_period | Hours for pattern | 24 |
| z_score_threshold | Anomaly threshold | 2.0 |

## Integration

### 1. Prometheus Integration

The metrics system exports Prometheus-compatible metrics:

```python
# prometheus_client setup
from prometheus_client import start_http_server, Gauge

# Export metrics
latency_gauge = Gauge('ai_gateway_latency', 'Request latency')
error_gauge = Gauge('ai_gateway_errors', 'Error count')

def export_metrics():
    metrics = validator.get_metrics_summary()
    latency_gauge.set(metrics["p95_latency"])
    error_gauge.set(metrics["error_count"])
```

### 2. Grafana Dashboards

Example Grafana dashboard configuration:

```json
{
  "dashboard": {
    "title": "AI Gateway Metrics",
    "panels": [
      {
        "title": "Latency Trends",
        "type": "graph",
        "targets": [
          {
            "expr": "ai_gateway_latency",
            "legendFormat": "P95 Latency"
          }
        ]
      },
      {
        "title": "Error Rates",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_gateway_errors[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      }
    ]
  }
}
```

### 3. Alerting Rules

Example alerting configuration:

```yaml
groups:
  - name: ai_gateway_alerts
    rules:
      - alert: HighLatency
        expr: ai_gateway_latency > 5000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High latency detected
          
      - alert: HighErrorRate
        expr: rate(ai_gateway_errors[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
```

## Best Practices

1. **Metric Collection**
   - Record all API endpoints
   - Include relevant context in details
   - Use consistent naming patterns

2. **Trend Analysis**
   - Collect enough data points (>30)
   - Consider seasonality in patterns
   - Validate trend significance

3. **Feature Metrics**
   - Track core usage metrics
   - Monitor user satisfaction
   - Analyze retention patterns

4. **Integration**
   - Use standard metric names
   - Set appropriate alert thresholds
   - Configure proper retention periods

## Troubleshooting

Common issues and solutions:

1. **Missing Metrics**
   - Check recording calls
   - Verify window size
   - Validate cleanup settings

2. **False Anomalies**
   - Adjust z-score threshold
   - Increase min_data_points
   - Check seasonality period

3. **Integration Issues**
   - Verify Prometheus endpoint
   - Check metric name conflicts
   - Validate dashboard queries 