# Caching Architecture in PepperPy

This document explains the relationship between the different caching systems in PepperPy:
- `pepperpy/caching/`: Primary caching framework
- `pepperpy/memory/cache.py`: Agent-specific memory caching
- `pepperpy/optimization/caching/`: Performance optimization caching

## Architecture Overview

PepperPy implements a multi-layered caching architecture to address different caching needs:

```
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│ pepperpy/caching/               │     │ pepperpy/memory/cache.py        │
│ (Primary Caching Framework)     │     │ (Agent Memory Caching)          │
│                                 │     │                                 │
│ - General-purpose caching       │     │ - Agent context caching         │
│ - Multiple storage backends     │     │ - Short-term memory             │
│ - Serialization support         │     │ - Interaction history           │
│ - Cache invalidation            │     │ - Relevance-based prioritization│
└───────────────┬─────────────────┘     └─────────────────────────────────┘
                │                                        ▲
                │ extends                                │
                ▼                                        │
┌─────────────────────────────────┐                      │
│ pepperpy/optimization/caching/  │                      │
│ (Performance Optimization)      │     specialized for  │
│                                 │ ────────────────────┘
│ - Request caching               │
│ - Result memoization            │
│ - Distributed caching           │
│ - Cache policies                │
└─────────────────────────────────┘
```

## Responsibilities

### Primary Caching (`pepperpy/caching/`)

The primary caching module provides:

1. **Core Caching Framework**: Base classes and interfaces for all caching in the system
2. **Storage Backends**: Support for in-memory, file-based, and distributed caching
3. **Serialization**: Flexible serialization/deserialization of cached objects
4. **Cache Management**: TTL, invalidation strategies, and cache statistics
5. **Vector Caching**: Specialized support for caching vector embeddings

This module serves as the foundation for all caching in PepperPy.

### Agent Memory Caching (`pepperpy/memory/cache.py`)

The agent memory caching module provides:

1. **Context Awareness**: Caching optimized for agent context and state
2. **Relevance Prioritization**: Prioritizing cache entries based on relevance to current context
3. **Adaptive Expiration**: Dynamic TTL based on information importance
4. **Selective Compression**: Compressing less frequently accessed information
5. **Temporary Knowledge**: Managing ephemeral information needed by agents

This module is specialized for agent-specific memory management needs.

### Performance Optimization Caching (`pepperpy/optimization/caching/`)

The optimization caching module provides:

1. **Request Caching**: Caching API requests to reduce external calls
2. **Result Memoization**: Caching function results for expensive operations
3. **Distributed Caching**: Shared cache for distributed deployments
4. **Cache Policies**: Sophisticated policies for cache management
5. **Performance Focus**: Optimized for reducing latency and resource usage

This module extends the primary caching framework with performance-focused features.

## Usage Guidelines

- **General Caching Needs**: Use `pepperpy/caching/`
- **Agent Memory Management**: Use `pepperpy/memory/cache.py`
- **Performance Optimization**: Use `pepperpy/optimization/caching/`

## Integration Points

The caching systems are designed to work together:

1. **Shared Interfaces**: Common interfaces allow interoperability
2. **Layered Approach**: Each layer builds on the capabilities of the layer below
3. **Specialized Implementations**: Each module provides specialized implementations for its domain

## Future Direction

In future versions, we plan to:

1. Further unify the caching architecture
2. Provide a more consistent API across all caching modules
3. Implement more sophisticated cache eviction strategies
4. Add better monitoring and observability for cache performance

## Example: Using Different Caching Systems

```python
# Primary caching for general use
from pepperpy.caching import Cache
general_cache = Cache()
general_cache.set("key", "value", ttl=3600)
value = general_cache.get("key")

# Agent memory caching
from pepperpy.caching.memory_cache import ContextCache
context_cache = ContextCache()
context_cache.add_to_context("user_preference", {"theme": "dark"})
preferences = context_cache.get_from_context("user_preference")

# Performance optimization caching
from pepperpy.optimization.caching import RequestCache
request_cache = RequestCache()
result = request_cache.get_or_fetch("api/endpoint", fetch_function)
``` 