# AI Gateway Monitoring

This directory contains the monitoring setup for the AI Gateway, including metrics collection and visualization.

## Components

- `metrics.py`: Prometheus metrics collector implementation
- `grafana/`: Grafana dashboard configurations
- `prometheus/`: Prometheus configuration (if needed)

## Metrics Overview

The following metrics are collected:

- **Request Metrics**
  - Total requests (`ai_gateway_requests_total`)
  - Request duration (`ai_gateway_request_duration_seconds`)
  - Request errors (`ai_gateway_errors_total`)

- **Model Metrics**
  - Model latency (`ai_gateway_model_latency_seconds`)
  - Token usage (`ai_gateway_token_usage_total`)

- **Feature Usage**
  - Feature usage counts (`ai_gateway_feature_usage_total`)

- **System Status**
  - System up/down status (`ai_gateway_system_status`)

## Setup

1. Ensure Prometheus is installed and configured to scrape the AI Gateway metrics endpoint:

```yaml
scrape_configs:
  - job_name: 'ai_gateway'
    static_configs:
      - targets: ['localhost:9090']
```

2. Import the Grafana dashboard:
   - Navigate to Grafana > Dashboards > Import
   - Upload the `grafana/ai_gateway_dashboard.json` file
   - Select your Prometheus data source

## Dashboard Features

The Grafana dashboard provides:

- Request rate and latency monitoring
- System status indicator
- Feature usage distribution
- Token usage by model
- Error tracking

## Usage

The metrics collector automatically starts with the AI Gateway. Metrics are exposed at:
- Prometheus metrics: `http://localhost:9090/metrics`
- Grafana dashboard: Available after import at your Grafana instance

## Alerting

Configure alerts in Grafana based on:
- High error rates
- Latency spikes
- System status changes
- Token usage thresholds

## Development

To add new metrics:

1. Add metric definitions to `MetricsCollector` class
2. Update the Grafana dashboard as needed
3. Document new metrics in this README 