# PepperPy Caching Architecture

This document explains the relationship between the different caching systems in the PepperPy framework.

## Overview

PepperPy implements a multi-layered caching architecture with specialized caching systems for different use cases:

1. **Unified Caching System (`pepperpy/caching/`)**: The primary caching framework with comprehensive features.
2. **Memory Caching (`pepperpy/memory/cache.py`)**: Agent-specific caching focused on context awareness.
3. **Optimization Caching (`pepperpy/optimization/caching/`)**: Performance-oriented caching for API requests and computations.

## Unified Caching System (`pepperpy/caching/`)

The unified caching system serves as the primary caching framework with comprehensive features:

- **Base Functionality**: Common interfaces, serialization, and entry management.
- **Memory Caching**: In-memory storage with LRU/TTL policies and thread-safe operations.
- **Distributed Caching**: Redis backend with cluster support and pub/sub capabilities.
- **Vector Caching**: Specialized caching for vector embeddings and similarity search.
- **Migration Support**: Tools for migrating cache data between versions.

Key components:
- `base.py`: Core interfaces and base classes
- `memory.py`: In-memory cache implementation
- `distributed.py`: Distributed cache implementation
- `vector.py`: Vector-specific cache implementation
- `migration.py`: Cache migration utilities

## Agent Memory Caching (`pepperpy/memory/cache.py`)

The agent memory caching system is optimized for agent context and conversational state:

- **Context Cache**: Stores interaction history, agent state, and short-term memory.
- **Relevance-Based Prioritization**: Prioritizes cache entries based on relevance to current context.
- **Adaptive Expiration**: Adjusts expiration times based on importance and recency.
- **Selective Compression**: Compresses less frequently accessed data.

This system is specifically designed for agent-specific use cases rather than general performance optimization.

## Optimization Caching (`pepperpy/optimization/caching/`)

The optimization caching system focuses on performance optimization for API requests and computations:

- **Data Cache**: Stores computation results, frequent data, and external resources.
- **Expiration Policy**: Configurable expiration policies for different types of data.
- **Size Limits**: Enforces cache size limits to prevent memory issues.
- **Distribution**: Supports distributed caching for multi-node deployments.

Key components:
- `local.py`: Local cache implementation
- `distributed.py`: Distributed cache implementation
- `policy.py`: Cache policy configuration

## Integration and Relationships

The three caching systems are designed to work together while serving different purposes:

1. **Unified Caching (`pepperpy/caching/`)**: 
   - Provides the foundation for all caching in the framework
   - Offers the most comprehensive feature set
   - Suitable for most general caching needs

2. **Memory Caching (`pepperpy/memory/cache.py`)**: 
   - Specializes in agent context and conversational state
   - Optimized for relevance and context awareness
   - Integrates with the agent memory system

3. **Optimization Caching (`pepperpy/optimization/caching/`)**: 
   - Focuses on performance optimization
   - Designed for high-throughput API requests
   - Emphasizes efficiency and resource conservation

## Usage Guidelines

- Use **Unified Caching** when:
  - You need comprehensive caching features
  - Working with vector embeddings
  - Requiring distributed caching with advanced features

- Use **Memory Caching** when:
  - Working with agent context and conversation history
  - Needing context-aware caching
  - Prioritizing relevance over raw performance

- Use **Optimization Caching** when:
  - Optimizing API request performance
  - Reducing resource load and bandwidth
  - Implementing simple caching with minimal overhead

## Future Development

The modular caching architecture allows for:
- Specialized optimization for different use cases
- Independent evolution of caching strategies
- Clear separation of concerns for maintenance and testing 