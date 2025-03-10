# PepperPy Language Models Module

This module provides abstractions and implementations for working with Large Language Models (LLMs) in PepperPy. It provides a unified interface for interacting with different LLM providers.

## Overview

The LLM module provides a consistent interface for working with different LLM providers, such as OpenAI, Anthropic, Google Gemini, and others. It abstracts away the differences between these providers, allowing you to switch between them with minimal code changes.

## Core Components

- **LLMMessage**: Standard message format for LLM interactions
- **LLMResponse**: Standard response format from LLM providers
- **CompletionOptions**: Configuration options for LLM completions
- **ModelParameters**: Parameters and capabilities of an LLM model
- **LLMProviderBase**: Base class for all LLM providers
- **ModelCapability**: Enumeration of model capabilities
- **ModelInfo**: Information about an LLM model
- **ModelRegistry**: Registry of available models

## Module Structure

- `core.py`: Core functionality and base classes
- `public.py`: Public API for the module
- `providers/`: Implementations of various LLM providers
  - `core.py`: Core provider functionality
  - `openai/`: OpenAI provider implementation
  - `anthropic/`: Anthropic provider implementation
  - `gemini/`: Google Gemini provider implementation
  - `perplexity/`: Perplexity provider implementation
  - `openrouter/`: OpenRouter provider implementation

## Usage Example

```python
from pepperpy.llm import create_provider, LLMMessage

# Create an LLM provider
provider = create_provider("openai", api_key="your-api-key")

# Generate text from a prompt
response = await provider.generate("Hello, world!")
print(response.content)

# Generate a response from a conversation
messages = [
    LLMMessage(role="system", content="You are a helpful assistant."),
    LLMMessage(role="user", content="What is the capital of France?"),
]
response = await provider.generate_response(messages)
print(response.content)
```

## Supported Providers

- **OpenAI**: GPT-3.5, GPT-4, etc.
- **Anthropic**: Claude, Claude 2, etc.
- **Google Gemini**: Gemini Pro, Gemini Ultra, etc.
- **Perplexity**: Perplexity models
- **OpenRouter**: Access to multiple models through OpenRouter

## Creating Custom Providers

You can create custom providers by extending the `LLMProviderBase` class:

```python
from pepperpy.llm import LLMProviderBase, LLMResponse, register_provider

class MyCustomProvider(LLMProviderBase):
    """Custom LLM provider."""
    
    def __init__(self, **kwargs):
        """Initialize the provider."""
        # Custom initialization
        
    def generate(self, prompt, options=None, **kwargs):
        """Generate text from a prompt."""
        # Custom implementation
        return LLMResponse(content="Generated text", model="my-model")
        
    # Implement other required methods
    
# Register the provider
register_provider("my-provider", MyCustomProvider)
``` 