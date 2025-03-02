# Module Standardization Guide

This document outlines the standardized structure for modules in the PepperPy framework to ensure consistency across the codebase.

## Module Structure

Each primary domain module should follow this structure:

```
pepperpy/{domain}/
├── __init__.py           # Module initialization and exports
├── base.py               # Base classes and interfaces
├── types.py              # Type definitions and enums
├── factory.py            # Factory for creating components
├── registry.py           # Registry for component registration
├── processors/           # Data processing components
│   ├── __init__.py
│   ├── README.md         # Documentation for processors
│   └── {processor}.py    # Specific processor implementations
├── providers/            # Provider implementations
│   ├── __init__.py
│   ├── README.md         # Documentation for providers
│   └── {provider}.py     # Specific provider implementations
└── README.md             # Module documentation
```

## Naming Conventions

1. **Directory Names**: Use singular form for module names (e.g., `workflow` instead of `workflows`).
2. **Processor Directories**: Use `processors/` for components that process or transform data.
3. **Provider Directories**: Use `providers/` for implementations of external services.
4. **Implementation Files**: Place concrete implementations in appropriate subdirectories rather than in an `implementations/` directory.

## Core Components

Every domain module should include these core components:

1. **Base Classes** (`base.py`): Abstract base classes and interfaces that define the contract for the domain.
2. **Type Definitions** (`types.py`): Type definitions, enums, and constants for the domain.
3. **Factory** (`factory.py`): Factory classes for creating instances of domain components.
4. **Registry** (`registry.py`): Registry for registering and retrieving domain components.

## Documentation

Each module and subdirectory should include:

1. **Module Documentation**: A README.md file explaining the purpose and usage of the module.
2. **Docstrings**: Comprehensive docstrings for all classes and functions.
3. **Examples**: Usage examples in the documentation.

## Migration Plan

When migrating existing modules to this standardized structure:

1. Create the new structure without removing the old one.
2. Update imports in the new structure to point to the old structure.
3. Gradually migrate components to the new structure.
4. Update imports in dependent modules.
5. Remove the old structure once migration is complete.

## Examples

### Before (Non-Standard):

```
pepperpy/workflows/
├── __init__.py
├── implementations/
│   ├── __init__.py
│   └── {implementation}.py
```

### After (Standardized):

```
pepperpy/workflow/
├── __init__.py
├── base.py
├── types.py
├── factory.py
├── registry.py
├── processors/
│   ├── __init__.py
│   └── {processor}.py
```