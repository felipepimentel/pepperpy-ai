# PepperPy Plugin System

PepperPy's plugin system allows you to extend the framework with custom providers for various capabilities like language models (LLM), text-to-speech (TTS), retrieval-augmented generation (RAG), and more. This document describes how to use and create plugins using the YAML configuration-based approach.

## Using Plugins

PepperPy automatically discovers and loads plugins from the `plugins` directory. Each plugin is organized in a domain-specific subdirectory, such as `plugins/llm/openai` for an OpenAI LLM provider.

### Loading a Plugin

To use a plugin, you can create a provider instance directly:

```python
from pepperpy.plugins.registry import create_provider_instance

# Create an OpenAI LLM provider
provider = await create_provider_instance(
    "llm",                   # Plugin type
    "openai",                # Provider name
    api_key="your-api-key",  # Configuration
    model="gpt-4-turbo"
)

# Use the provider
result = await provider.generate(messages)
```

Or use it with the PepperPy class:

```python
from pepperpy import PepperPy

pepper = PepperPy()
pepper.with_plugin(
    "llm",                   # Plugin type  
    "openai",                # Provider name
    api_key="your-api-key",  # Configuration
    model="gpt-4-turbo"
)

# Use the framework with the plugin
response = await pepper.ask_query("What is artificial intelligence?")
```

## Creating Custom Plugins

To create a custom plugin, you need to define a provider class and a YAML configuration file.

### Plugin Structure

A typical plugin has the following structure:

```
plugins/
└── {domain}/
    └── {provider}/
        ├── plugin.yaml
        ├── provider.py
        └── requirements.txt
```

For example:

```
plugins/
└── llm/
    └── openai/
        ├── plugin.yaml
        ├── provider.py
        └── requirements.txt
```

### YAML Configuration

The `plugin.yaml` file defines the plugin's metadata, configuration schema, and dependencies:

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
    temperature:
      type: number
      description: Sampling temperature (0-1)
      default: 0.7

metadata:
  provider_url: https://openai.com/
  requires_api_key: true

dependencies:
  - openai>=1.0.0
```

### Provider Implementation

The provider class implements the domain-specific interface:

```python
from pepperpy.llm import LLMProvider, Message
from pepperpy.plugin import ProviderPlugin

class OpenAIProvider(LLMProvider, ProviderPlugin):
    """OpenAI LLM provider implementation."""
    
    # Type-annotated config attributes that match plugin.yaml schema
    api_key: str
    model: str = "gpt-4-turbo"
    temperature: float = 0.7
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return
            
        # Create client and initialize resources
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.initialized = True
        
    async def generate(self, messages: List[Message], **kwargs) -> GenerationResult:
        """Generate a response from the LLM."""
        # Implementation details...
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.close()
            self.client = None
        self.initialized = False
```

### Dependencies

The `requirements.txt` file lists the dependencies required by your plugin:

```
# Plugin dependencies
openai>=1.0.0
tiktoken>=0.5.0
```

These dependencies are automatically installed when the plugin is loaded, ensuring that your plugin has all the necessary libraries without affecting the main project's requirements.

## Plugin Types

PepperPy supports various plugin types:

1. **LLM** (`llm`): Language model providers (OpenAI, Anthropic, etc.)
2. **TTS** (`tts`): Text-to-speech providers
3. **RAG** (`rag`): Retrieval-augmented generation providers
4. **Content** (`content`): Content generation providers
5. **Embedding** (`embedding`): Embedding providers
6. **Workflow** (`workflow`): Workflow providers

Each type has its own interface that your provider must implement.

## Plugin Discovery

Plugins are discovered automatically from the following directories:

1. `plugins/` (relative to the current working directory)
2. `~/plugins/pepperpy/` (user plugins directory)
3. Any custom directories registered with `register_plugin_path()`

## Plugin Configuration

Plugins can be configured in several ways:

1. **Direct configuration** when creating a provider:
   ```python
   provider = await create_provider_instance("llm", "openai", api_key="...")
   ```

2. **Environment variables**:
   ```
   OPENAI_API_KEY=your-api-key
   ```

3. **Configuration files** in YAML format:
   ```yaml
   # ~/.pepperpy/config.yaml
   plugins:
     llm:
       openai:
         api_key: your-api-key
         model: gpt-4-turbo
   ```

## Example Plugins

### LLM Provider (OpenAI)

```yaml
# plugins/llm/openai/plugin.yaml
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
```

```python
# plugins/llm/openai/provider.py
from pepperpy.llm import LLMProvider, Message, GenerationResult
from pepperpy.plugin import ProviderPlugin

class OpenAIProvider(LLMProvider, ProviderPlugin):
    # Implementation details...
```

### TTS Provider (Basic)

```yaml
# plugins/tts/basic/plugin.yaml
name: basic
version: 0.1.0
description: Basic text-to-speech provider using system voices
author: PepperPy Team
type: tts
provider_class: BasicTTSProvider

config_schema:
  type: object
  properties:
    voice:
      type: string
      description: System voice to use
      default: "default"
    rate:
      type: number
      description: Speaking rate (1.0 is normal speed)
      default: 1.0
```

```python
# plugins/tts/basic/provider.py
from pepperpy.tts.base import TTSProvider, TTSVoice
from pepperpy.plugin import ProviderPlugin

class BasicTTSProvider(TTSProvider, ProviderPlugin):
    # Implementation details...
```

### RAG Provider (Local)

```yaml
# plugins/rag/local/plugin.yaml
name: local
version: 0.1.0
description: Local RAG provider using filesystem storage
author: PepperPy Team
type: rag
provider_class: LocalRAGProvider

config_schema:
  type: object
  properties:
    storage_path:
      type: string
      description: Path for storing embeddings and documents
      default: "./data/rag"
```

```python
# plugins/rag/local/provider.py
from pepperpy.rag import RAGProvider, Document, SearchResult
from pepperpy.plugin import ProviderPlugin

class LocalRAGProvider(RAGProvider, ProviderPlugin):
    # Implementation details...
```

## Best Practices

1. **Use typed attributes** that match your YAML schema
2. **Implement proper initialization and cleanup** methods
3. **Handle errors gracefully** and provide meaningful error messages
4. **Document your plugin** with clear descriptions of configuration options
5. **Specify dependencies** in `requirements.txt`
6. **Follow the naming conventions** for plugins (lowercase names)
7. **Use async/await** for all I/O operations

## Plugin Lifecycle

1. **Discovery**: Plugin is found in the plugins directory
2. **Loading**: Plugin metadata is read from `plugin.yaml`
3. **Initialization**: Provider is instantiated with configuration
4. **Usage**: Provider methods are called by the application
5. **Cleanup**: Resources are released when the provider is no longer needed

By following this guide, you can create and use custom plugins to extend PepperPy's functionality with your own implementations. 