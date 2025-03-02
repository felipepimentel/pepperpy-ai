# Provider Standardization Strategy

## Current Situation

The PepperPy framework currently has a mixed approach to provider organization:

1. **Centralized approach**: A central `pepperpy/providers/` directory contains provider implementations for various domains (embedding, cloud, llm, storage, vision, config, agent, audio).

2. **Distributed approach**: Some domain-specific modules like `embedding/providers/` and `memory/providers/` have their own provider implementations.

3. **Public API**: Each domain module now has a `public.py` file that exposes a unified public API for that domain.

## Standardization Strategy

### 1. Centralized Provider Approach

We will adopt a fully centralized approach for all providers in the PepperPy framework:

- **All providers will be located in domain-specific directories** (e.g., `llm/providers/`, `embedding/providers/`)
- **Each domain directory will have a consistent structure**:
  - `__init__.py`: Exports the public API for the domain
  - `public.py`: Defines the public interfaces for the domain
  - `base.py`: Base classes and interfaces for the domain
  - `providers/`: Directory containing provider implementations

### 2. Migration Plan

1. **Identify all distributed provider implementations**:
   - `embedding/providers/`
   - `memory/providers/`
   - Any other domain-specific provider directories

2. **Move provider implementations to the domain-specific structure**:
   - Move implementation files to `{domain}/providers/`
   - Ensure consistent naming and structure

3. **Create backward compatibility layer**:
   - Add import redirects in the original locations
   - Use the existing migration utilities in `pepperpy/migration.py`
   - Add deprecation warnings for the old import paths

4. **Update the public API**:
   - Ensure each domain has a `public.py` file that exports the public interfaces
   - Maintain a consistent public interface

5. **Update documentation and examples**:
   - Update all documentation to reflect the new structure
   - Update examples to use the new import paths

### 3. Provider Structure Standard

Each domain should follow this standard structure:

```
pepperpy/{domain}/
├── __init__.py           # Exports the public API
├── public.py             # Public interfaces
├── base.py               # Base classes and interfaces
└── providers/            # Provider implementations
    ├── __init__.py       # Exports provider implementations
    └── {implementation}.py  # Provider implementations
```

### 4. Import Patterns

- **Internal imports**: Use direct imports from the domain-specific location
  ```python
  from pepperpy.llm.providers.openai import OpenAIProvider
  ```

- **Public API imports**: Use the domain's public interfaces
  ```python
  from pepperpy.llm.providers import OpenAIProvider
  ```

### 5. Implementation Timeline

1. **Phase 1**: Move all distributed providers to the domain-specific structure
2. **Phase 2**: Add backward compatibility layer
3. **Phase 3**: Update documentation and examples
4. **Phase 4**: Deprecate old import paths (with warnings)
5. **Phase 5**: Remove backward compatibility in a future major version

## Benefits

1. **Consistency**: A single, consistent approach to provider organization
2. **Discoverability**: Makes it easier to find and manage all providers
3. **Maintainability**: Simplifies dependency management and imports
4. **Extensibility**: Clear pattern for adding new provider types
5. **API Stability**: Maintains a stable public API through the domain-specific public interfaces