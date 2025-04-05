# Discovery and Plugins Relationship

## Overview

PepperPy is designed with a clear separation of concerns between the `discovery` and `plugins` subsystems. This document clarifies their relationship and responsibilities.

## Responsibilities

### Discovery Module (`pepperpy.discovery`)

The Discovery module provides **low-level discovery mechanisms** for:

1. Service discovery - Finding available services
2. Content type detection - Analyzing and identifying content types
3. Basic plugin discovery interfaces - Core abstract interfaces for plugin discovery

This module is intentionally small and focused, providing the fundamental infrastructure for discovering components within the PepperPy ecosystem.

### Plugins Module (`pepperpy.plugins`)

The Plugins module provides **high-level plugin management** for:

1. Plugin lifecycle - Loading, initializing, and cleanup
2. Plugin registration - Managing the plugin registry
3. Plugin dependency resolution - Handling dependencies between plugins
4. Plugin configuration - Loading and validating plugin configs
5. Advanced plugin discovery - Implementing discovery using the interfaces from the discovery module

This module is more extensive and handles the complete plugin management lifecycle, building on the discovery interfaces provided by the Discovery module.

## Interaction Diagram

```
┌───────────────────┐             ┌───────────────────┐
│     Discovery     │             │      Plugins      │
│    (Low Level)    │             │    (High Level)   │
└─────────┬─────────┘             └─────────┬─────────┘
          │                                 │
          │ Provides                        │ Provides
          ▼                                 ▼
┌───────────────────┐             ┌───────────────────┐
│  Base Interfaces  │◄────Uses────┤  Implementation   │
│  & Abstractions   │             │   & Management    │
└───────────────────┘             └───────────────────┘
```

## Design Rationale

1. **Separation of Concerns**
   - Discovery handles fundamental mechanisms
   - Plugins handles complete lifecycle management

2. **Extensibility**
   - New discovery mechanisms can be added independently
   - Plugin system can evolve without changing discovery interfaces

3. **Testability**
   - Discovery mechanisms can be tested in isolation
   - Plugin system can be tested with mock discovery providers

## Best Practices

1. **For Framework Developers**
   - Add core interfaces to `discovery.base`
   - Implement high-level plugin management in `plugins`
   - Don't duplicate functionality between modules

2. **For Plugin Developers**
   - Use the plugin system APIs, not discovery directly
   - Follow the plugin registration patterns
   - Don't try to interact with discovery mechanisms directly

## Migration Path

For existing code that might be using both systems independently:

1. Use the plugin system for plugin registration and discovery
2. Use discovery only for content-type detection and service discovery
3. If both are being used, prefer the plugin system API

## Conclusion

By understanding the separation between low-level discovery mechanisms and high-level plugin management, we maintain a cleaner architecture with proper separation of concerns. 