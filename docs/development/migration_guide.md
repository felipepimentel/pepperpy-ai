# Migration Guide

This guide helps you migrate your code to the new PepperPy structure.

## Import Changes

### Core Module Changes
- `from pepperpy.common` → `from pepperpy.core.utils`
- `from pepperpy.config` → `from pepperpy.core.config`
- `from pepperpy.context` → `from pepperpy.core.context`
- `from pepperpy.lifecycle` → `from pepperpy.core.lifecycle`

### Provider Changes
- `from pepperpy.llms` → `from pepperpy.providers.llm`
- `from pepperpy.embeddings` → `from pepperpy.providers.embedding`
- `from pepperpy.vector_store` → `from pepperpy.providers.vector_store`
- `from pepperpy.memory` → `from pepperpy.providers.memory`

### Tool Changes
- `from pepperpy.tools` → `from pepperpy.capabilities.tools`
- `from pepperpy.tools.functions` → `from pepperpy.capabilities.tools.functions`

### Data Module Changes
- `from pepperpy.data.vector` → `from pepperpy.providers.vector_store.base`
- `from pepperpy.data.document` → `from pepperpy.persistence.storage.document`
- `from pepperpy.data_stores.chunking` → `from pepperpy.persistence.storage.chunking`
- `from pepperpy.data_stores.conversation` → `from pepperpy.persistence.storage.conversation`
- `from pepperpy.data_stores.memory` → `from pepperpy.providers.memory`
- `from pepperpy.data_stores.rag` → `from pepperpy.persistence.storage.rag`
- `from pepperpy.data_stores.embedding_manager` → `from pepperpy.providers.embedding`
- `from pepperpy.data_stores.vector_db` → `from pepperpy.providers.vector_store`
- `from pepperpy.data_stores.document_store` → `from pepperpy.persistence.storage.document`

## Class Name Changes

### Provider Classes
- `BaseLLM` → `BaseLLMProvider`
- `BaseEmbedding` → `BaseEmbeddingProvider`
- `BaseVectorStore` → `BaseVectorStoreProvider`
- `BaseMemory` → `BaseMemoryProvider`

### Tool Classes
- `BaseTool` → `BaseCapability`
- All tool classes are now capabilities

## Configuration Changes

### Provider Configuration
```python
# Old format
config = {
    "llm": {
        "type": "openrouter",
        "model": "anthropic/claude-2"
    }
}

# New format
config = {
    "providers": {
        "llm": {
            "type": "openrouter",
            "model_name": "anthropic/claude-2"
        }
    }
}
```

### Tool Configuration
```python
# Old format
tool_config = {
    "name": "serp",
    "api_key": "your-api-key"
}

# New format
capability_config = {
    "name": "serp_search",
    "config": {
        "api_key": "your-api-key"
    }
}
```

## Breaking Changes

1. Provider Registry
   - Providers must now be registered using the `@Provider.register()` decorator
   - Provider names must be unique across all provider types

2. Capability System
   - Tools are now capabilities and must implement the `BaseCapability` interface
   - Capabilities must declare their dependencies and required providers
   - Capabilities must specify supported inputs and outputs

3. Persistence Layer
   - Data storage is now handled by the persistence layer
   - Vector operations are now part of the vector store provider
   - Document operations are now part of the storage module

4. Error Handling
   - Provider-specific errors now inherit from `PepperpyError`
   - Each module has its own error class (e.g., `PersistenceError`, `CapabilityError`)

## Migration Steps

1. Update Imports
   - Use the import changes table above to update your imports
   - Remove any deprecated imports

2. Update Provider Usage
   - Register your providers using the new decorator
   - Update provider configurations to the new format
   - Use the new provider base classes

3. Update Tool Usage
   - Convert tools to capabilities
   - Update tool configurations to the new format
   - Implement required capability methods

4. Update Data Access
   - Use the persistence layer for data storage
   - Update vector operations to use vector store providers
   - Update document operations to use storage module

5. Update Error Handling
   - Use the new error classes
   - Update error handling code

## Example Migration

```python
# Old code
from pepperpy.llms import BaseLLM
from pepperpy.tools import SerpSearchTool

class MyLLM(BaseLLM):
    async def generate(self, prompt: str) -> str:
        pass

tool = SerpSearchTool(api_key="key")

# New code
from pepperpy.providers.llm import BaseLLMProvider
from pepperpy.capabilities.tools.functions.serp import SerpSearchCapability

@BaseLLMProvider.register("my_llm")
class MyLLM(BaseLLMProvider):
    async def generate(self, prompt: str) -> str:
        pass

capability = SerpSearchCapability(
    name="serp_search",
    config={"api_key": "key"}
)
```

## Need Help?

If you encounter any issues during migration:
1. Check the API reference documentation
2. Review the example code in the `examples/` directory
3. Open an issue on GitHub for support 