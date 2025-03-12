# PepperPy Refactoring Guide

This document provides an overview of the recent refactoring of the PepperPy library and guidance for migrating existing code to the new structure.

## Overview

The PepperPy library has been refactored to improve maintainability, reduce code duplication, and provide a more consistent and intuitive API. The main changes include:

1. **Consolidated Provider Framework**: A unified base provider interface with common functionality for all providers.
2. **REST-based Providers**: A common REST provider base class for all providers that interact with REST APIs.
3. **Centralized Registry**: A registry system for discovering and instantiating providers dynamically.
4. **Standardized Module Structure**: Consistent patterns for module organization and public APIs.
5. **Improved Type System**: Consolidated type definitions for better type safety and consistency.

## Migration Guide

### Provider Imports

The provider implementations have been consolidated, but backward compatibility is maintained. You can continue to import providers from their original locations:

```python
# Old imports still work
from pepperpy.llm.providers.openai import OpenAIProvider
from pepperpy.llm.providers.anthropic import AnthropicProvider

# New recommended imports
from pepperpy.llm.providers import OpenAIProvider, AnthropicProvider
```

### Provider Initialization

Provider initialization remains largely the same, but with some improvements:

```python
# Old initialization
provider = OpenAIProvider(
    api_key="your-api-key",
    model="gpt-3.5-turbo",
)

# New initialization (more consistent across providers)
provider = OpenAIProvider(
    api_key="your-api-key",
    default_model="gpt-3.5-turbo",
)
```

### Using the Registry

The new registry system allows for dynamic discovery and instantiation of providers:

```python
from pepperpy.core.registry import registry

# Register a provider
registry.register("llm", "openai", OpenAIProvider)

# Create a provider instance
provider = registry.create_provider("llm", "openai", api_key="your-api-key")

# List available providers
providers = registry.list_providers("llm")
```

### REST-based Providers

If you're implementing custom providers that interact with REST APIs, you can now extend the `RESTProvider` base class:

```python
from pepperpy.providers.rest_base import RESTProvider

class MyCustomProvider(RESTProvider):
    def _get_default_base_url(self) -> str:
        return "https://api.example.com/v1"
        
    async def my_custom_method(self, data):
        response = await self._make_request(
            method="POST",
            endpoint="custom-endpoint",
            data=data,
        )
        return response
```

### LLM Module Changes

The LLM module now provides a more consistent interface:

```python
import pepperpy as pp

# Generate text
result = await pp.llm.generate("Explain quantum computing in simple terms")

# Generate embeddings
result = await pp.llm.embed("Quantum computing")

# Use a specific provider
result = await pp.llm.generate(
    "Explain quantum computing in simple terms",
    provider="anthropic",
    model="claude-2",
)
```

### RAG Module Changes

The RAG module now includes REST-based providers for embedding, reranking, and generation:

```python
from pepperpy.rag.providers import (
    RESTEmbeddingProvider,
    RESTRerankingProvider,
    RESTGenerationProvider,
)

# Create embedding provider
embedding_provider = RESTEmbeddingProvider(
    name="my-embedding-provider",
    api_key="your-api-key",
    default_model="text-embedding-ada-002",
    base_url="https://api.example.com",
)

# Create reranking provider
reranking_provider = RESTRerankingProvider(
    name="my-reranking-provider",
    api_key="your-api-key",
    default_model="rerank-v1",
    base_url="https://api.example.com",
)

# Create generation provider
generation_provider = RESTGenerationProvider(
    name="my-generation-provider",
    api_key="your-api-key",
    default_model="gpt-3.5-turbo",
    base_url="https://api.example.com",
)
```

### Data Module Changes

The Data module now includes a REST-based provider for data storage and retrieval:

```python
from pepperpy.data.providers import RESTDataProvider

# Create data provider
data_provider = RESTDataProvider(
    name="my-data-provider",
    api_key="your-api-key",
    base_url="https://api.example.com",
)

# Create a document
result = await data_provider.create(
    collection="my-collection",
    data={"key": "value"},
)

# Read a document
result = await data_provider.read(
    collection="my-collection",
    document_id="document-id",
)

# Update a document
result = await data_provider.update(
    collection="my-collection",
    document_id="document-id",
    data={"key": "new-value"},
)

# Delete a document
result = await data_provider.delete(
    collection="my-collection",
    document_id="document-id",
)

# Query documents
result = await data_provider.query(
    collection="my-collection",
    query={"key": "value"},
)
```

## Best Practices

1. **Use the Public API**: Prefer using the public API functions in the module's `__init__.py` file rather than importing internal components directly.

2. **Leverage the Registry**: Use the registry system for dynamic provider discovery and instantiation.

3. **Extend Base Classes**: When implementing custom providers, extend the appropriate base classes to ensure consistent behavior.

4. **Use Type Hints**: Take advantage of the consolidated type definitions in `pepperpy/types/common.py` for better type safety.

5. **Follow the Module Pattern**: When adding new modules, follow the established pattern of `core.py`, `public.py`, and `__init__.py` files.

## Examples

See the `examples/` directory for complete examples of using the refactored library. 