# PepperPy Integration Plugin System

## Overview

The Integration Plugin System provides a standardized way to interact with external services and APIs. Integration plugins are specialized components that handle the communication with external services, providing a clean abstraction layer for other components in the PepperPy framework.

## Directory Structure

```
plugins/
└── integration/
    ├── base.py                # Core interfaces and factory functions
    ├── specs/                 # API specifications (OpenAPI, etc.)
    │   └── weather_api.yaml   # Weather API spec
    └── weather/               # Weather integration domain
        └── openweather/       # OpenWeather API implementation
            ├── plugin.yaml    # Plugin metadata
            ├── provider.py    # OpenWeather API provider implementation
            └── __init__.py    # Package initialization
```

## Usage

### Creating an Integration Plugin

1. Create the directory structure:
```bash
mkdir -p plugins/integration/<domain>/<implementation>
```

2. Create a plugin.yaml file with the plugin metadata:
```yaml
name: implementation_name
version: 0.1.0
description: Description of the integration
author: Author Information

plugin_type: integration
category: domain
provider_name: implementation_name
entry_point: provider.ImplementationProvider

config_schema:
  type: object
  properties:
    api_key:
      type: string
      description: API key for the service
    # Additional configuration options

default_config:
  # Default configuration values
```

3. Implement the provider:
```python
"""Integration provider implementation."""

import logging
from typing import Any, Dict, Optional
from pepperpy.integration import IntegrationProvider, IntegrationError

class ImplementationProvider(IntegrationProvider):
    """Provider for the integration."""
    
    # Type-annotated config attributes
    api_key: str
    
    async def initialize(self) -> None:
        """Initialize provider resources."""
        if self._initialized:
            return
        
        # Initialize resources
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        # Clean up resources
```

### Using an Integration Plugin

From a workflow or other component:

```python
from pepperpy.integration import create_integration_provider

# Create and initialize the integration provider
integration = create_integration_provider(
    provider_type="domain",
    provider_name="implementation",
    api_key="your-api-key",
    # Additional configuration
)
await integration.initialize()

try:
    # Use the integration
    result = await integration.some_method()
    # Process the result
finally:
    # Clean up resources
    await integration.cleanup()
```

## API Specifications

The `specs/` directory contains API specifications in OpenAPI format for the external services that are integrated with PepperPy. These specs can be used for:

- Documentation
- Code generation
- Testing
- Request validation

For example, the Weather API specification describes the endpoints for retrieving weather information.

## Development Guidelines

When developing an integration plugin:

1. **Error Handling**: Always wrap external API calls in try-except blocks and convert external exceptions to `IntegrationError`
2. **Type Annotations**: Use proper type annotations for configuration parameters and method signatures
3. **Initialization**: Always implement proper resource initialization and cleanup
4. **Configuration**: Access configuration parameters through self-attributes
5. **Documentation**: Document all methods with docstrings including parameters and return values
6. **Testing**: Write tests for the integration provider, including mocking external API calls

## Best Practices

- Use aiohttp for HTTP requests to ensure async compatibility
- Implement proper rate limiting and error handling for external APIs
- Cache responses when appropriate to improve performance and reduce API calls
- Use environment variables for sensitive information like API keys 