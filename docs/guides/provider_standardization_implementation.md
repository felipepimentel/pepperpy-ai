# Provider Standardization Implementation Guide

This guide provides step-by-step instructions for implementing the provider standardization strategy in the PepperPy framework.

## Overview

The provider standardization strategy aims to create a consistent approach to provider organization by:

1. Moving all providers to a centralized `pepperpy/providers/` directory
2. Organizing providers by domain subdirectories
3. Ensuring a consistent structure for each provider domain
4. Maintaining backward compatibility through import redirects
5. Providing a unified public API through the interfaces package

## Prerequisites

- Python 3.8+
- Access to the PepperPy codebase
- Understanding of the [Provider Standardization Strategy](../provider_standardization.md)

## Implementation Steps

### 1. Prepare the Environment

Ensure you have the latest version of the codebase:

```bash
git pull origin main
```

### 2. Run the Provider Migration Script

The migration script will move all distributed provider implementations to the centralized structure:

```bash
python scripts/migrate_providers.py
```

This script:
- Identifies all distributed provider implementations
- Moves provider files to the centralized structure
- Creates backward compatibility layers in the original locations
- Updates the provider mapping in `pepperpy/migration.py`

### 3. Update the Public API

Run the provider API update script to update the public API in `interfaces/providers/__init__.py`:

```bash
python scripts/update_provider_api.py
```

This script:
- Scans all provider domains in the centralized `pepperpy/providers/` directory
- Finds all provider classes
- Updates the `interfaces/providers/__init__.py` file with imports and exports

### 4. Run Tests

Run the test suite to ensure everything is working correctly:

```bash
pytest
```

Fix any issues that arise from the migration.

### 5. Update Documentation and Examples

Update documentation and examples to use the new import paths:

- For internal imports, use the centralized location:
  ```python
  from pepperpy.providers.llm.openai import OpenAIProvider
  ```

- For public API imports, use the interfaces package:
  ```python
  from pepperpy.interfaces.providers import OpenAIProvider
  ```

### 6. Creating New Providers

To create new provider implementations, use the provider creation script:

```bash
# Create a new domain
python scripts/create_provider.py domain_name

# Create a new provider implementation
python scripts/create_provider.py domain_name provider_name
```

After creating new providers, update the public API:

```bash
python scripts/update_provider_api.py
```

## Provider Structure Standard

Each provider domain should follow this standard structure:

```
pepperpy/providers/{domain}/
├── __init__.py           # Exports the public API
├── base.py               # Base classes and interfaces
└── {implementation}.py   # Provider implementations
```

## Backward Compatibility

The migration process creates backward compatibility layers in the original locations. These layers:

1. Emit deprecation warnings when used
2. Import and re-export the providers from the new location
3. Will be removed in a future major version

Example of a compatibility layer:

```python
"""
Compatibility layer for providers that have been moved to the centralized structure.

This module provides backward compatibility for code that imports from the old location.
It will be removed in a future version.
"""

from pepperpy.migration import provider_migration_warning

# Emit a deprecation warning
provider_migration_warning("embedding.providers", "providers.embedding")

# Import from the new location
from pepperpy.providers.embedding import *
```

## Troubleshooting

### Import Errors

If you encounter import errors after migration:

1. Check that the backward compatibility layers are in place
2. Ensure the imports in your code match the new structure
3. Run the provider API update script again

### Missing Providers in the Public API

If providers are missing from the public API:

1. Ensure the provider class name ends with "Provider"
2. Run the provider API update script again
3. Check that the provider is properly exported in its domain's `__init__.py`

## Next Steps

1. Gradually update all code to use the new import paths
2. Monitor for deprecation warnings and address them
3. Plan for the removal of backward compatibility in a future major version