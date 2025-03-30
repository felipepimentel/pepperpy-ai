# PepperPy Plugin System

The PepperPy framework uses a lightweight, easy-to-implement plugin system that allows users to extend
functionality with minimal overhead. Plugins are loaded dynamically and managed using UV for 
dependency installation, which offers better performance and reliability compared to pip.

## Plugin Directory Structure

Plugins must follow this directory structure:

```
plugins/
├── llm_openai/                  # Plugin directory (follows naming convention)
│   ├── __init__.py              # Package initialization
│   ├── provider.py              # Provider implementation (business logic only)
│   ├── plugin.yaml              # Plugin metadata (SINGLE SOURCE OF TRUTH)
│   ├── README.md                # Plugin documentation
│   └── requirements.txt         # Dependencies (installed via UV)
└── ...                          # Other plugins
```

## Plugin Directory Naming Convention

Plugin directories should follow this naming convention:

```
{domain}_{provider}
```

Examples:
- `llm_openai` - OpenAI LLM provider
- `llm_anthropic` - Anthropic LLM provider
- `rag_chroma` - Chroma vector store RAG provider
- `tts_elevenlabs` - ElevenLabs TTS provider

## Plugin Metadata - Single Source of Truth

The most important file in a plugin is `plugin.yaml`, which defines all the metadata for the plugin.
This ensures that business logic in `provider.py` is separate from configuration metadata.

```yaml
# OpenAI Provider Plugin Metadata
name: llm_openai
version: 0.1.0
description: OpenAI provider for PepperPy
category: llm
provider_type: openai
author: PepperPy Team
required_config_keys:
  - api_key
```

The metadata is automatically loaded and applied to the provider class at runtime, eliminating duplication.

## Required Files

Each plugin must contain the following files:

### 1. `plugin.yaml`

The single source of truth for plugin metadata:

```yaml
# Plugin metadata
name: domain_provider
version: 1.0.0
description: Provider for PepperPy
category: domain
provider_type: provider
author: PepperPy Team
required_config_keys:
  - api_key
```

### 2. `provider.py`

Provider implementation class that inherits from the appropriate base provider and `ProviderPlugin`.
The provider class focuses only on business logic with no metadata:

```python
from pepperpy.domain import DomainProvider
from pepperpy.plugin import ProviderPlugin

class MyProvider(DomainProvider, ProviderPlugin):
    """Provider implementation."""
    
    def __init__(self, api_key=None, **kwargs):
        """Initialize provider.
        
        The API key will be automatically injected from environment
        variables if not provided explicitly.
        """
        super().__init__(api_key=api_key, **kwargs)
        
    async def initialize(self):
        """Initialize resources."""
        # Business logic here
        # Access environment variables via self._config
        # Logging via self.logger
        
    async def process(self, data):
        """Process data."""
        # Business logic here
        self.logger.debug("Processing data")
```

### 3. `__init__.py`

Package initialization file that imports the provider:

```python
"""Provider for PepperPy."""

from .provider import MyProvider

__all__ = ["MyProvider"]
```

### 4. `README.md`

Documentation for the plugin:

```markdown
# Provider for PepperPy

This plugin provides ... integration for the PepperPy framework.

## Usage

```python
from pepperpy import PepperPy

app = PepperPy()
result = await app.domain.provider().process("data")
```

## Configuration

...
```

### 5. `requirements.txt`

Dependencies for the plugin (installed using UV):

```
# PepperPy plugin dependencies
external-package>=1.0.0
# No need to include dependencies provided by PepperPy core
```

## Built-in Utilities - No Manual Setup Required

PepperPy provides built-in utilities that plugins can use without any manual setup:

### Logger

Each provider automatically gets a logger that you can access via `self.logger`:

```python
def process(self, data):
    self.logger.debug("Processing data")  # No need to initialize logger
    self.logger.info("Operation completed")
```

### Environment Variables

Environment variables are automatically injected for all keys listed in `required_config_keys`:

```python
def __init__(self, api_key=None, **kwargs):
    # api_key will be loaded from environment variables if not provided:
    # 1. PEPPERPY_LLM__OPENAI__API_KEY
    # 2. OPENAI_API_KEY
    # 3. PEPPERPY_API_KEY
    super().__init__(api_key=api_key, **kwargs)
```

### Error Handling

Use PepperPy's built-in error types for consistent error handling:

```python
from pepperpy.core import ConfigError, ProviderError

def process(self, data):
    if not self.client:
        raise ProviderError("Client not initialized")
```

## Creating a New Plugin

### Step 1: Create Plugin Directory

```bash
mkdir -p plugins/domain_provider
```

Example: `mkdir -p plugins/llm_openai`

### Step 2: Create Basic Files

1. Create `plugin.yaml` with metadata:
   ```yaml
   # Plugin metadata
   name: domain_provider
   version: 1.0.0
   description: Provider for PepperPy
   category: domain
   provider_type: provider
   author: PepperPy Team
   required_config_keys:
     - api_key
   ```

2. Create `provider.py` with implementation focusing on business logic:
   ```python
   """Provider implementation."""
   
   from pepperpy.domain import DomainProvider
   from pepperpy.plugin import ProviderPlugin
   
   class MyProvider(DomainProvider, ProviderPlugin):
       """Provider implementation."""
       
       def __init__(self, api_key=None, **kwargs):
           super().__init__(api_key=api_key, **kwargs)
           
       async def initialize(self):
           # Business logic - the logger and config are already available
           self.logger.debug("Initializing provider")
           
       async def cleanup(self):
           # Business logic
           pass
   ```

3. Create `__init__.py`:
   ```python
   """Provider for PepperPy."""

   from .provider import MyProvider

   __all__ = ["MyProvider"]
   ```

4. Create `README.md` with documentation.

5. Create `requirements.txt` with external dependencies only:
   ```
   # List only external dependencies not provided by PepperPy
   external-package>=1.0.0
   ```

## Plugin Discovery

The plugin system automatically discovers plugins based on:

1. Metadata in the `plugin.yaml` file
2. The directory structure in the `plugins/` directory

## Benefits of This Approach

1. **Separation of Concerns**: Metadata in `plugin.yaml`, business logic in `provider.py`
2. **Built-in Utilities**: Logger, environment variables, and error handling provided automatically
3. **Minimal Code**: Focus on business logic without boilerplate
4. **Clean Provider Implementation**: No class variables for metadata
5. **PepperPy Utilities**: Built-in logging, error handling, and configuration management
6. **Minimal Dependencies**: Only include external dependencies not provided by PepperPy

## Example

See `examples/plugin_example.py` for a complete example of installing and using plugins with the UV-based system. 