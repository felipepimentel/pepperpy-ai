# PepperPy YAML-Based Plugin System Implementation

This document summarizes the implementation of the YAML-based plugin system in PepperPy, which provides a flexible and extensible way to integrate new capabilities into the framework.

## Core Components

### 1. Plugin Interface (`pepperpy/plugin.py`)

The central interface that all provider plugins inherit from, providing:
- Configuration binding with type annotations
- Initialization and cleanup lifecycle methods
- Access to configuration values and utilities

```python
class ProviderPlugin(PepperpyPlugin):
    """Base class for PepperPy provider plugins using the YAML configuration system."""
    
    @property
    def initialized(self) -> bool:
        """Check if the provider is initialized."""
        return getattr(self, "_initialized", False)
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return
        self.initialized = True
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        self.initialized = False
```

### 2. YAML Configuration Format

A standardized YAML structure for defining plugins:

```yaml
name: openai
version: 0.2.0
description: OpenAI provider for language model tasks
author: PepperPy Team
type: llm
provider_class: OpenAIProvider

config_schema:
  type: object
  required:
    - api_key
  properties:
    api_key:
      type: string
      description: OpenAI API key
    model:
      type: string
      description: OpenAI model to use
      default: gpt-4-turbo

metadata:
  provider_url: https://openai.com/
  requires_api_key: true

dependencies:
  - openai>=1.0.0
```

### 3. Provider Registry (`pepperpy/plugin/registry.py`)

Handles:
- Plugin discovery
- Loading configuration
- Creating provider instances
- Dependency management

```python
async def create_provider_instance(
    plugin_type: str,
    provider_type: str,
    **config: Any
) -> Any:
    """Create a provider instance.

    Args:
        plugin_type: Type of plugin (e.g., "llm", "tts")
        provider_type: Type of provider (e.g., "openai", "basic")
        **config: Configuration to pass to provider

    Returns:
        Provider instance
    """
    # Implementation details...
```

## Implemented Plugins

### 1. LLM Provider (OpenAI)

Integration with OpenAI's API for language model capabilities.

Key features:
- Support for multiple models (GPT-4, etc.)
- Full configuration options (temperature, tokens, etc.)
- Streaming support
- Error handling and resource management

### 2. TTS Provider (Basic)

Text-to-speech implementation using system voices with pyttsx3.

Key features:
- Support for multiple system voices
- Configurable voice parameters (rate, volume, etc.)
- Async operation for non-blocking synthesis
- Proper resource cleanup

### 3. RAG Provider (Local)

Local Retrieval-Augmented Generation using LangChain and ChromaDB.

Key features:
- Document storage and retrieval
- Vector-based semantic search
- Multiple file format support (PDF, DOCX, TXT, etc.)
- Configurable chunking and embedding

## Examples

### Example 1: Using the OpenAI LLM Provider

```python
from pepperpy.plugin.registry import create_provider_instance
from pepperpy.llm import Message, MessageRole

provider = await create_provider_instance(
    "llm", 
    "openai", 
    api_key="your-api-key", 
    model="gpt-4-turbo"
)

messages = [
    Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
    Message(role=MessageRole.USER, content="Tell me a joke about programming.")
]

result = await provider.generate(messages)
print(result.content)

await provider.cleanup()
```

### Example 2: Using the TTS Provider

```python
from pepperpy.plugin.registry import create_provider_instance

provider = await create_provider_instance(
    "tts", 
    "basic", 
    rate=1.2, 
    volume=0.8
)

# List available voices
voices = await provider.get_available_voices()
voice_id = voices[0].id if voices else "default"

# Convert text to speech
result = await provider.synthesize(
    text="Hello, this is a test of text to speech!",
    voice_id=voice_id,
    output_path="output.wav"
)

await provider.cleanup()
```

### Example 3: Using the RAG Provider

```python
from pepperpy.plugin.registry import create_provider_instance
from pepperpy.rag import Document

provider = await create_provider_instance(
    "rag", 
    "local", 
    storage_path="./data/rag"
)

# Add a document
doc = Document(
    text="PepperPy is a powerful Python framework for AI applications.",
    metadata={"source": "documentation", "type": "overview"}
)
await provider.store(doc)

# Search for documents
results = await provider.search("Python framework")
for result in results:
    print(f"Score: {result.score}, Text: {result.text}")

await provider.cleanup()
```

## Integration with PepperPy

The plugin system is fully integrated with the main PepperPy framework, allowing:

1. Direct creation of provider instances
2. Automatic discovery and loading of plugins
3. On-demand installation of plugin dependencies
4. Configuration through environment variables or config files
5. Seamless integration with the PepperPy class

## Benefits

1. **Reduced boilerplate code** - Standardized patterns across providers
2. **Easy extensibility** - Add new providers with minimal code
3. **Automatic configuration binding** - Type-annotated attributes match YAML schema
4. **Proper resource management** - Initialization and cleanup handled automatically
5. **Dependency isolation** - Provider-specific requirements don't affect main project
6. **Clear documentation** - YAML schema provides self-documenting configuration

## Future Enhancements

1. **Plugin versioning** - Support for managing plugin versions
2. **Plugin hot-reloading** - Dynamically reload plugins without restart
3. **Plugin interoperability** - Allow plugins to interact with each other
4. **Plugin hooks** - Add lifecycle hooks for advanced plugin behavior
5. **Plugin documentation generation** - Automatic docs from YAML schema

## Conclusion

The YAML-based plugin system provides a flexible, maintainable, and user-friendly approach to extending the PepperPy framework. It allows developers to easily add new capabilities without modifying the core codebase. 