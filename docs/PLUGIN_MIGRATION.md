# PepperPy Plugin Migration Guide

This document outlines the migration to the new UV-based plugin system in PepperPy.

## Overview of Changes

We've implemented several improvements to the plugin system:

1. **Simplified directory structure**: Flattened the plugin hierarchy to reduce complexity
2. **UV-based dependency management**: Replaced Poetry with UV for faster, more reliable dependency management
3. **Separation of concerns**: Plugin metadata in plugin.yaml, business logic in provider.py
4. **Built-in utilities**: Logger, environment variables, and error handling injected automatically
5. **Auto-discovery**: Enhanced the plugin manager to automatically discover and register plugins
6. **On-demand installation**: Added support for automatic dependency installation when plugins are used

## Directory Structure Changes

### Old Structure

```
plugins/
└── llm_openai_provider/         # Extra "provider" suffix
    └── pepperpy_llm_openai/     # Unnecessary nesting
        ├── __init__.py
        └── provider.py
```

### New Structure

```
plugins/
└── llm_openai/                 # Simple domain_provider naming
    ├── __init__.py
    ├── provider.py             # Only business logic, no metadata
    ├── plugin.yaml             # Plugin metadata, separate from code
    ├── README.md
    └── requirements.txt        # Only external dependencies
```

## Dependency Management Changes

### Old Approach: Poetry

Previously, we used Poetry for dependency management with pyproject.toml:

```toml
[tool.poetry]
name = "pepperpy-llm-openai"
version = "0.1.0"
# ...

[tool.poetry.dependencies]
python = "^3.10"
openai = "^1.12.0"
loguru = "^0.7.0"  # Third-party logging library
# ...
```

### New Approach: UV with Only External Dependencies

Now, we use UV with simple requirements.txt containing only external dependencies:

```
# PepperPy plugin dependencies
openai>=1.12.0
# No third-party utilities - use PepperPy's built-in systems
```

Benefits:
- 10-100x faster installation
- Simpler dependency specification
- Better dependency resolution
- On-demand installation
- No duplication of utilities already provided by PepperPy

## Plugin Implementation Changes

### Old Approach: Metadata in Code

```python
# In provider.py - mixing business logic with metadata
class OpenAIProvider(LLMProvider):
    name = "openai"
    
    def __init__(self, api_key=None):
        # Manual environment variable handling
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise Exception("API key not found")
        
    def generate(self, prompt):
        # Manual logging
        logger.info("Generating text")
```

### New Approach: Separation of Concerns

#### plugin.yaml - Metadata only
```yaml
# Metadata in separate file
name: llm_openai
version: 0.1.0
description: OpenAI provider for PepperPy
category: llm
provider_type: openai
required_config_keys:
  - api_key
```

#### provider.py - Business logic only
```python
# No metadata or boilerplate, just business logic
class OpenAIProvider(LLMProvider, ProviderPlugin):
    def __init__(self, api_key=None, **kwargs):
        # Environment variables automatically injected
        super().__init__(api_key=api_key, **kwargs)
        
    def generate(self, prompt):
        # Logger automatically available
        self.logger.info("Generating text")
```

## Migration Steps

To migrate an existing plugin to the new system:

1. **Create the new directory structure**:
   ```bash
   mkdir -p plugins/domain_provider
   ```

2. **Create plugin.yaml for metadata**:
   ```yaml
   name: domain_provider
   version: 1.0.0
   description: Provider for PepperPy
   category: domain
   provider_type: provider
   author: PepperPy Team
   required_config_keys:
     - api_key
   ```

3. **Simplify provider.py to focus on business logic**:
   ```python
   from pepperpy.domain import DomainProvider
   from pepperpy.plugin import ProviderPlugin
   
   class MyProvider(DomainProvider, ProviderPlugin):
       # No metadata class variables needed
       
       def __init__(self, api_key=None, **kwargs):
           # No manual environment variable handling needed
           super().__init__(api_key=api_key, **kwargs)
           
       def process(self, data):
           # Use automatic logger
           self.logger.debug("Processing data")
   ```

4. **Create requirements.txt with only external dependencies**:
   ```
   # Only external dependencies not provided by PepperPy
   external-package>=1.0.0
   ```

5. **Simplify __init__.py**:
   ```python
   """Provider for PepperPy."""
   from .provider import MyProvider
   __all__ = ["MyProvider"]
   ```

## Using the New Plugin System

### Installing Plugin Dependencies

```python
from pepperpy import install_plugin_dependencies, plugin_manager

# Install a specific plugin
install_plugin_dependencies("llm_openai")

# Install all plugins
plugin_manager.install_all_plugins()
```

### Using Plugins

```python
from pepperpy import PepperPy

async with PepperPy().with_llm(provider_type="openai") as pepper:
    result = await pepper.chat.with_user("Hello!").generate()
    print(result.content)
```

## Advantages of the New System

1. **Separation of concerns**: Metadata in plugin.yaml, business logic in provider.py
2. **No boilerplate**: Logger, environment variables, and error handling provided automatically
3. **Clean implementation**: Focus only on business logic in provider classes
4. **Faster installation**: UV is much faster than pip/poetry
5. **On-demand dependencies**: Dependencies installed only when needed
6. **Auto-discovery**: Plugins are automatically discovered
7. **Dynamic installation**: Missing dependencies can be installed automatically

See the full documentation in `docs/plugin_structure.md` and examples in `examples/plugin_example.py`. 