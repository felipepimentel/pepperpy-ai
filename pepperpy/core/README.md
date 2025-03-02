# Core Module Structure

## Overview

The `core` module provides the foundational components and utilities for the PepperPy framework. It is organized into several submodules, each with a specific purpose.

## Structure

- **base**: Base classes and interfaces for components and providers
  - `BaseComponent`: Abstract base class for all components
  - `BaseProvider`: Base class for all providers
  - `BaseManager`: Generic manager for components
  - `Lifecycle`: Base class for components with lifecycle management
  - `ComponentConfig`: Configuration for components
  - `ComponentCallback`: Protocol for component callbacks

- **common**: Common utilities and shared components
  - `utils`: Utility functions for common operations
  - `types`: Core types and enumerations

- **validation**: Validation utilities and schemas
  - `ValidationError`: Base exception for validation errors
  - `Validator`: Base class for all validators
  - `SchemaDefinition`: Schema definition for validation
  - `ValidationManager`: Manager for validation

- **types**: Core type definitions
  - `JsonDict`, `JsonList`: Type aliases for JSON data
  - `PathLike`: Type alias for path-like objects
  - `Version`: Version representation

- **registry**: Component registry system
  - `Registry`: Registry for components
  - `ComponentMetadata`: Metadata for components

## Recent Improvements

1. **Consolidated Validation**: Moved validation functionality from `core/common/validation` to `core/validation` to eliminate duplication.

2. **Consolidated Base Classes**: Merged functionality from `core/common/base.py` and `core/base/common.py` into `core/base/__init__.py` to provide a unified base component system.

3. **Removed Empty Files**: Removed empty or unused utility files (`validation.py`, `formatting.py`, `system.py`, `io.py`, `data_manipulation.py`) from `core/common/utils` and additional empty files (`client.py`, `factory.py`, `recovery.py`, `models.py`, `lazy.py`, `optional.py`) from various locations.

4. **Consistent Naming**: Ensured consistent naming across modules.

5. **Reduced Redundancy**: Eliminated overlapping functionality between modules.

## Usage Guidelines

- Import base classes from `pepperpy.core.base`
- Import validation utilities from `pepperpy.core.validation`
- Import common utilities from `pepperpy.core.common.utils`
- Import type definitions from `pepperpy.core.types`

## Example

```python
from pepperpy.core.base import BaseComponent, Lifecycle
from pepperpy.core.validation import Validator
from pepperpy.core.types import JsonDict

class MyComponent(BaseComponent, Lifecycle):
    def __init__(self, name: str):
        super().__init__(name)
        # Component implementation
    
    async def _initialize(self) -> None:
        # Initialize resources
        pass
        
    async def _cleanup(self) -> None:
        # Clean up resources
        pass
```
