# PepperPy Observability Architecture

This document explains the relationship between the `core/observability` and `observability` modules in the PepperPy framework.

## Architecture Overview

PepperPy's observability system is organized into two complementary modules:

1. **Core Observability (`pepperpy/core/observability/`)**: Provides the fundamental infrastructure and interfaces for observability.
2. **Domain-Specific Observability (`pepperpy/observability/`)**: Implements specialized observability features for AI-specific use cases.

## Core Observability (`pepperpy/core/observability/`)

The core observability module provides the foundational infrastructure for all observability features:

- **Base Interfaces**: Defines the core abstractions and interfaces for metrics, logging, tracing, and monitoring.
- **Infrastructure**: Implements the core observability manager, collectors, and integration points.
- **Framework Integration**: Provides hooks for framework components to report their state.

Key components:
- `base.py`: Core interfaces and base classes
- `logging/`: Structured logging system
- `metrics/`: Metrics collection and reporting
- `monitoring/`: System monitoring capabilities
- `health/`: Health check infrastructure
- `audit/`: Audit logging for security and compliance

## Domain-Specific Observability (`pepperpy/observability/`)

The domain-specific observability module builds on the core infrastructure to provide AI-specific observability features:

- **AI-Specific Metrics**: Specialized metrics for AI model performance, latency, and quality.
- **Cost Tracking**: Monitoring and reporting of API usage costs.
- **Hallucination Detection**: Tools for detecting and reporting model hallucinations.
- **Model Performance**: Detailed performance metrics for AI models.

Key components:
- `model_performance.py`: AI model performance tracking
- `cost_tracking.py`: API cost monitoring and budgeting
- `hallucination_detection.py`: Detection of model hallucinations
- `metrics/`: AI-specific metrics implementations
- `tracing/`: AI workflow tracing
- `health/`: AI-specific health checks
- `monitoring/`: AI system monitoring

## Integration Points

The two modules are integrated through:

1. **Inheritance**: Domain-specific components inherit from core interfaces.
2. **Composition**: Domain-specific components use core infrastructure.
3. **Registration**: Domain-specific components register with the core observability manager.

## Usage Guidelines

- Use `core/observability` when:
  - Implementing framework-level observability
  - Creating new observability interfaces
  - Integrating with external observability systems

- Use `observability` when:
  - Monitoring AI-specific metrics
  - Tracking costs and performance
  - Implementing domain-specific health checks
  - Detecting AI-specific issues like hallucinations

## Future Development

The separation allows for:
- Independent evolution of core infrastructure and domain-specific features
- Clear boundaries for testing and maintenance
- Flexibility in implementing new observability features 