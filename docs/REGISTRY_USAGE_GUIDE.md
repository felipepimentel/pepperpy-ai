# Registry Usage Guide

This document provides guidelines for using the unified registry system in the PepperPy framework. Following these guidelines ensures consistency across the framework and makes it easier to maintain and extend the codebase.

## Overview

The PepperPy registry system provides a centralized mechanism for registering and discovering components across different modules. It consists of the following key components:

1. **Registry**: A generic container for components of a specific type
2. **RegistryComponent**: Base class for all components that can be registered
3. **RegistryManager**: Global manager for all registries
4. **Auto-registration utilities**: Tools for automatically registering components

## Core Registry Structure

The core registry system is located in `pepperpy/core/registry/` and consists of:

- `base.py`: Core registry classes and functionality
- `auto.py`: Auto-registration utilities
- `__init__.py`: Public API exports

## Recommended Usage Pattern

### 1. Creating a Domain-Specific Registry

Each domain (agents, workflows, RAG, etc.) should have its own registry module that follows this pattern:

```python
"""Domain registry module for the PepperPy framework.

This module provides registry functionality for managing domain components.
"""

from typing import Optional, Type

from pepperpy.core.registry import (
    ComponentMetadata,
    Registry,
    RegistryComponent,
    get_registry,
)
from pepperpy.domain.base import BaseDomainComponent

# Configure logging
from pepperpy.core.logging import get_logger
logger = get_logger(__name__)


class DomainRegistry(Registry[BaseDomainComponent]):
    """Registry for managing domain components."""

    def __init__(self) -> None:
        """Initialize domain registry."""
        super().__init__(BaseDomainComponent)
        
        # Register built-in components
        # self.register_type("component_name", ComponentClass)


# Global registry instance
_registry: Optional[DomainRegistry] = None


def get_domain_registry() -> DomainRegistry:
    """Get the global domain registry instance.

    Returns:
        Domain registry instance
    """
    global _registry
    if _registry is None:
        _registry = DomainRegistry()
        # Register with the global registry manager
        try:
            registry_manager = get_registry()
            registry_manager.register_registry("domain_name", _registry)
        except Exception as e:
            logger.warning(f"Failed to register with global registry: {e}")
    return _registry
```

### 2. Creating Registry Components

Components that can be registered should inherit from `RegistryComponent`:

```python
from pepperpy.core.registry import ComponentMetadata, RegistryComponent


class MyComponent(RegistryComponent):
    """My custom component."""

    def __init__(self, name: str, description: str = ""):
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    @property
    def metadata(self) -> ComponentMetadata:
        """Get component metadata."""
        return ComponentMetadata(
            name=self.name,
            description=self._description,
            tags={"custom"},
            properties={"type": "example"},
        )
```

### 3. Auto-Registration

For automatic component registration, use the decorators provided in `pepperpy.core.registry.auto`:

```python
from pepperpy.core.registry.auto import register_component

@register_component("domain_name", "component_name")
class MyAutoComponent(RegistryComponent):
    """Component with auto-registration."""
    
    # Component implementation
```

### 4. Using the Registry

To use a domain-specific registry:

```python
from pepperpy.domain.registry import get_domain_registry

# Get registry
registry = get_domain_registry()

# Get component
component = registry.get("component_name")

# Create component from registered type
new_component = registry.create("component_type", arg1, arg2, kwarg1=value1)
```

## Compliance Checks

To ensure your registry implementation follows the recommended pattern, run:

```bash
python scripts/check_registry_compliance.py
```

This script checks for:

1. Proper imports from `pepperpy.core.registry`
2. Registry class inheritance from `Registry`
3. Presence of a `get_*_registry()` function
4. Registration with the global registry manager

## Best Practices

1. **Single Registry Per Domain**: Each domain should have a single registry module
2. **Lazy Initialization**: Use the singleton pattern with lazy initialization
3. **Global Registration**: Always register domain registries with the global registry manager
4. **Descriptive Metadata**: Provide detailed metadata for components
5. **Error Handling**: Handle registration errors gracefully
6. **Documentation**: Document registry components and their usage

## Example

See `examples/registry_example.py` for a complete example of using the registry system.

## Migration from Legacy Registry

If you're migrating from the legacy registry system:

1. Update imports to use `pepperpy.core.registry` instead of `pepperpy.core.common.registry`
2. Run `scripts/fix_registry_imports.py` to automatically fix imports
3. Ensure your registry implementation follows the recommended pattern
4. Run `scripts/check_registry_compliance.py` to verify compliance