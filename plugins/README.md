# PepperPy Plugins

This directory contains plugins for the PepperPy framework, organized by their domain type.

## Overview

PepperPy's plugin system allows extending the framework with custom providers for various capabilities. Each plugin is defined using a YAML configuration file and a provider implementation class.

## Plugin Structure

Each plugin follows this structure:

```
plugins/
└── {domain}/                 # Domain type (llm, tts, rag, etc.)
    └── {provider}/           # Provider name (openai, basic, local, etc.)
        ├── plugin.yaml       # Plugin configuration and metadata
        ├── provider.py       # Provider implementation
        └── requirements.txt  # Plugin-specific dependencies
```

## Available Plugins

### LLM Providers

- `openai`: OpenAI API integration for language models (GPT-4, etc.)

### TTS Providers

- `basic`: System text-to-speech using pyttsx3

### RAG Providers

- `local`: Local RAG provider using LangChain and ChromaDB

## Creating a Plugin

To create a new plugin:

1. Create a directory for your plugin under the appropriate domain
2. Create a `plugin.yaml` file with your plugin's metadata and configuration schema
3. Implement the provider class in `provider.py`
4. Add any dependencies to `requirements.txt`

See the [Plugin System Documentation](../docs/plugins.md) for more details.

## Plugin Discovery

The framework automatically discovers plugins in this directory. No additional registration is required.

## Example Usage

```python
from pepperpy.plugins.registry import create_provider_instance

# Create an OpenAI LLM provider
provider = await create_provider_instance("llm", "openai", api_key="your-api-key")

# Use the provider
result = await provider.generate(messages)
``` 