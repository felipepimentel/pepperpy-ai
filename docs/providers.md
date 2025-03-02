# Provider Approach in PepperPy

## Overview

The Provider Pattern is a core architectural pattern in the PepperPy framework. It enables the framework to support multiple implementations of the same functionality, allowing users to choose the implementation that best suits their needs without changing their application code.

## Provider Pattern

A provider in PepperPy is an implementation of a specific interface that delivers a particular capability. For example, an LLM provider implements the LLM interface to provide language model capabilities from services like OpenAI, Anthropic, or Hugging Face.

### Key Benefits

1. **Abstraction**: Providers abstract away the implementation details of specific services or technologies.
2. **Interchangeability**: Applications can switch between different providers with minimal code changes.
3. **Consistency**: All providers for a given domain follow the same interface, ensuring consistent behavior.
4. **Extensibility**: New providers can be added without modifying existing code.
5. **Testability**: Mock providers can be used for testing without external dependencies.

## Provider Structure

### Provider Interface

Each domain has one or more interfaces that define the contract that providers must implement:

```python
# pepperpy/storage/public.py
from abc import ABC, abstractmethod
from typing import Any, BinaryIO, List, Optional, Union

class StorageProvider(ABC):
    """Interface for storage providers."""
    
    @abstractmethod
    def save(self, data: Union[str, bytes, BinaryIO], path: str) -> str:
        """Save data to storage."""
        pass
        
    @abstractmethod
    def load(self, path: str) -> Union[str, bytes]:
        """Load data from storage."""
        pass
```

### Provider Implementation

Providers implement the interface for a specific service or technology:

```python
# pepperpy/storage/providers/local.py
from pepperpy.storage import StorageProvider

class LocalStorageProvider(StorageProvider):
    """Local filesystem implementation of the storage provider interface."""
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = base_path
        
    def save(self, data: Union[str, bytes, BinaryIO], path: str) -> str:
        # Implementation details...
        pass
        
    def load(self, path: str) -> Union[str, bytes]:
        # Implementation details...
        pass
```

## Provider Organization

Providers are organized by domain in the `pepperpy/providers/` directory:

```
pepperpy/providers/
├── llm/                  # LLM providers
│   ├── openai.py         # OpenAI provider
│   ├── anthropic.py      # Anthropic provider
│   └── ...
├── storage/              # Storage providers
│   ├── local.py          # Local storage provider
│   ├── s3.py             # AWS S3 provider
│   └── ...
├── cloud/                # Cloud providers
│   ├── aws.py            # AWS provider
│   ├── gcp.py            # Google Cloud provider
│   └── ...
└── ...                   # Other domains
```

## Provider Registration

Providers are registered with the framework to make them discoverable:

```python
# Example provider registration
from pepperpy.core.registry import register_provider
from pepperpy.providers.llm.openai import OpenAIProvider

register_provider("llm", "openai", OpenAIProvider)
```

## Provider Factory

The factory pattern is used to create provider instances based on configuration:

```python
# Example factory usage
from pepperpy.factory import LLMFactory

# Create an LLM provider instance
llm_provider = LLMFactory.create("openai", api_key="your-api-key")
```

## Provider Configuration

Providers can be configured through:

1. **Constructor Parameters**: Passed when creating the provider instance
2. **Environment Variables**: Set in the environment
3. **Configuration Files**: Loaded from configuration files

Example:

```python
# Configuration through constructor parameters
provider = OpenAIProvider(api_key="your-api-key", model="gpt-4")

# Configuration through environment variables
# PEPPERPY_OPENAI_API_KEY=your-api-key
# PEPPERPY_OPENAI_MODEL=gpt-4
provider = OpenAIProvider()

# Configuration through configuration files
# config.yaml:
# providers:
#   openai:
#     api_key: your-api-key
#     model: gpt-4
provider = OpenAIProvider.from_config("config.yaml")
```

## Creating Custom Providers

To create a custom provider:

1. **Identify the Interface**: Determine which interface your provider should implement
2. **Create the Provider Class**: Implement the interface
3. **Register the Provider**: Register your provider with the framework

Example:

```python
# Custom LLM provider
from pepperpy.llm import LLMProvider
from pepperpy.core.registry import register_provider

class MyCustomLLMProvider(LLMProvider):
    """Custom LLM provider implementation."""
    
    def __init__(self, **kwargs):
        # Initialize your provider
        pass
        
    def generate(self, prompt: str, **kwargs) -> str:
        # Implement the generate method
        pass

# Register the provider
register_provider("llm", "my-custom", MyCustomLLMProvider)
```

## Provider Best Practices

1. **Follow the Interface**: Implement all methods defined in the interface
2. **Handle Errors Gracefully**: Catch provider-specific errors and convert them to framework errors
3. **Provide Sensible Defaults**: Make it easy to use your provider with minimal configuration
4. **Document Requirements**: Clearly document any dependencies or requirements
5. **Include Examples**: Provide examples of how to use your provider
6. **Write Tests**: Include tests for your provider

## Provider Capabilities

Providers can implement additional capabilities beyond the base interface:

```python
from pepperpy.llm import LLMProvider
from pepperpy.capabilities import StreamingCapable

class StreamingLLMProvider(LLMProvider, StreamingCapable):
    """LLM provider with streaming capability."""
    
    def generate(self, prompt: str, **kwargs) -> str:
        # Implementation...
        pass
        
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        # Streaming implementation...
        yield from chunks
```

## Provider Versioning

Providers should follow semantic versioning:

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

## Provider Migration

When migrating between provider versions, follow these steps:

1. **Check Compatibility**: Verify that the new provider version is compatible with your code
2. **Update Dependencies**: Update any dependencies required by the new provider version
3. **Test Thoroughly**: Test your application with the new provider version
4. **Update Configuration**: Update any configuration required by the new provider version

## Conclusion

The Provider Pattern is a powerful approach that enables the PepperPy framework to support multiple implementations of the same functionality. By following this pattern, the framework can be extended to support new services and technologies without changing the core codebase.
