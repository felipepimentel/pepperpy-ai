# Observability Architecture in PepperPy

This document explains the relationship between the two observability modules in PepperPy:
- `pepperpy/core/observability/`: Core observability interfaces and base implementations
- `pepperpy/observability/`: Extended observability features and implementations

## Architecture Overview

The observability system in PepperPy follows a layered architecture:

```
┌─────────────────────────────────────┐
│ pepperpy/observability/             │
│ (Extended Features & Implementations)│
│                                     │
│  - Health monitoring                 │
│  - Metrics collection                │
│  - Distributed tracing               │
│  - System monitoring                 │
│  - Cost tracking                     │
│  - Model performance                 │
│  - Hallucination detection           │
└───────────────┬─────────────────────┘
                │
                │ depends on
                ▼
┌─────────────────────────────────────┐
│ pepperpy/core/observability/        │
│ (Core Interfaces & Base Classes)     │
│                                     │
│  - Base interfaces                   │
│  - Abstract classes                  │
│  - Core functionality                │
│  - Integration points                │
└─────────────────────────────────────┘
```

## Responsibilities

### Core Observability (`pepperpy/core/observability/`)

The core observability module provides:

1. **Base Interfaces**: Abstract classes and interfaces that define the contract for all observability components
2. **Core Functionality**: Essential observability features required by the framework itself
3. **Integration Points**: Hooks and extension points for custom observability implementations
4. **Minimal Dependencies**: Designed to have minimal external dependencies to avoid bloating the core

This module is part of the framework's core and is always available, even in minimal installations.

### Extended Observability (`pepperpy/observability/`)

The extended observability module provides:

1. **Concrete Implementations**: Full implementations of the core interfaces
2. **Advanced Features**: Specialized observability features for specific use cases
3. **External Integrations**: Connectors to external monitoring systems and tools
4. **Optional Components**: Features that may have additional dependencies

This module builds upon the core interfaces but provides more comprehensive functionality for applications that need advanced observability features.

## Usage Guidelines

- **Framework Core**: Should only depend on `core/observability`
- **Applications**: Can use either module depending on their needs
- **Extensions**: Should build on top of `core/observability` interfaces
- **Custom Implementations**: Should implement the `core/observability` interfaces

## Future Direction

In future versions, we plan to:

1. Further standardize the interfaces between the two modules
2. Provide more pluggable implementations for different environments
3. Enhance the integration with external observability systems
4. Develop specialized observability features for AI-specific metrics

## Example: Metrics Collection

```python
# Using core interfaces
from pepperpy.core.observability import Counter, MetricsCollector

# Basic usage with core interfaces
counter = Counter("api_calls", "Number of API calls")
counter.increment()

# Using extended implementation
from pepperpy.observability.metrics import MetricsRegistry

# Advanced usage with extended features
registry = MetricsRegistry()
registry.register_counter("api_calls", "Number of API calls")
registry.increment_counter("api_calls")
registry.export_prometheus()
``` 