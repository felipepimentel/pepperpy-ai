# AI Providers Reference

PepperPy AI supports multiple AI providers through a unified interface.

## Supported Providers

### OpenAI
- [OpenAI Provider](./openai.md) - Integration with OpenAI's GPT models
- Features:
  - Text completion
  - Chat completion
  - Embeddings
  - Streaming support

### Anthropic
- [Anthropic Provider](./anthropic.md) - Integration with Anthropic's Claude models
- Features:
  - Text completion
  - Chat completion
  - Streaming support

### OpenRouter
- [OpenRouter Provider](./openrouter.md) - Integration with OpenRouter's API
- Features:
  - Access to multiple AI models
  - Unified API interface
  - Cost optimization

### StackSpot
- [StackSpot Provider](./stackspot.md) - Integration with StackSpot's AI services
- Features:
  - Specialized development tools
  - Code analysis
  - Project templates

## Provider Factory

The `ProviderFactory` makes it easy to create and manage providers:

```python
from pepperpy_ai.providers import ProviderFactory
from pepperpy_ai.config import Config

config = Config()
factory = ProviderFactory(config)

# Create an OpenAI provider
openai_provider = factory.create_provider("openai")

# Create an Anthropic provider
anthropic_provider = factory.create_provider("anthropic")
```

## Base Provider Interface

All providers implement the base provider interface:

```python
class BaseProvider(Protocol):
    """Base provider protocol."""
    
    @property
    def config(self) -> Config:
        """Get provider configuration."""
        ...
        
    async def complete(self, prompt: str) -> str:
        """Complete text prompt."""
        ...
        
    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream responses."""
        ...
        
    async def get_embedding(self, text: str) -> list[float]:
        """Get text embedding."""
        ...
```

## Provider Configuration

Providers can be configured through the config system:

```python
from pepperpy_ai.config import Config

config = Config(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4",
    temperature=0.7
)
```

## Provider Types

The following provider types are available:

- `openai` - OpenAI's GPT models
- `anthropic` - Anthropic's Claude models
- `openrouter` - OpenRouter's API
- `stackspot` - StackSpot's AI services

## Best Practices

1. **Provider Selection**
   - Choose providers based on your needs
   - Consider cost and performance
   - Use appropriate models for tasks

2. **Configuration**
   - Secure API key management
   - Configure appropriate parameters
   - Use environment variables

3. **Error Handling**
   - Handle provider-specific errors
   - Implement retries for transient failures
   - Use fallback providers

4. **Performance**
   - Use streaming for long responses
   - Implement request rate limiting
   - Monitor usage and costs

## Examples

### OpenAI Provider

```python
from pepperpy_ai.providers import ProviderFactory
from pepperpy_ai.config import Config

async def openai_example():
    config = Config(provider="openai")
    factory = ProviderFactory(config)
    provider = factory.create_provider("openai")
    
    response = await provider.complete("Explain Python generators")
    print(response)
```

### Anthropic Provider

```python
async def anthropic_example():
    config = Config(provider="anthropic")
    factory = ProviderFactory(config)
    provider = factory.create_provider("anthropic")
    
    response = await provider.complete("What are async functions?")
    print(response)
```

### Streaming Example

```python
async def streaming_example():
    config = Config()
    factory = ProviderFactory(config)
    provider = factory.create_provider("openai")
    
    async for chunk in provider.stream("Tell me about asyncio"):
        print(chunk, end="", flush=True)
```

## Environment Variables

Configure providers using environment variables:

```bash
# OpenAI
PEPPERPY_OPENAI_API_KEY=your-openai-key
PEPPERPY_OPENAI_MODEL=gpt-4

# Anthropic
PEPPERPY_ANTHROPIC_API_KEY=your-anthropic-key
PEPPERPY_ANTHROPIC_MODEL=claude-2

# OpenRouter
PEPPERPY_OPENROUTER_API_KEY=your-openrouter-key

# StackSpot
PEPPERPY_STACKSPOT_API_KEY=your-stackspot-key
``` 