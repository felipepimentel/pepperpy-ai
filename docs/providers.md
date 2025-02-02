# Provider System Documentation

The Pepperpy Provider System offers a unified, agnostic interface for interacting with various AI services. It provides a clean, type-safe API with support for multiple providers, streaming responses, and embeddings generation.

## Quick Start

```python
from pepperpy.providers import create_provider

# Create an OpenAI provider
provider = await create_provider(
    "openai",
    api_key="your-api-key",
    model="gpt-4"
)

# Complete a prompt
response = await provider.complete(
    "Explain quantum computing in simple terms.",
    temperature=0.7,
    max_tokens=200
)
print(response)

# Stream responses
async for chunk in await provider.complete(
    "Tell me a story...",
    stream=True
):
    print(chunk, end="", flush=True)

# Generate embeddings
embeddings = await provider.embed("Text to embed")
```

## Available Providers

### OpenAI
```python
provider = await create_provider(
    "openai",
    api_key="your-openai-key",
    model="gpt-4",  # or gpt-3.5-turbo
    timeout=30,
    max_retries=3
)
```

### Google Gemini
```python
provider = await create_provider(
    "gemini",
    api_key="your-gemini-key",
    model="gemini-pro",  # or gemini-pro-vision
    timeout=30,
    max_retries=3
)
```

### OpenRouter (Multi-Model)
```python
provider = await create_provider(
    "openrouter",
    api_key="your-openrouter-key",
    model="openai/gpt-4",  # or anthropic/claude-3
    timeout=30,
    max_retries=3,
    extra_config={
        "referer": "https://your-app.com",
        "title": "Your App"
    }
)
```

### StackSpot AI
```python
provider = await create_provider(
    "stackspot",
    api_key="your-stackspot-key",
    model="gpt-4",  # default model
    timeout=30,
    max_retries=3
)
```

## Provider Configuration

All providers accept a standard configuration through `ProviderConfig`:

```python
from pepperpy.providers import ProviderConfig

config = ProviderConfig(
    provider_type="openai",      # Required: Provider type
    api_key="your-api-key",      # Required: API key
    model="gpt-4",              # Optional: Model to use
    timeout=30,                 # Optional: Timeout in seconds
    max_retries=3,             # Optional: Max retries on failure
    extra_config={             # Optional: Provider-specific config
        "organization": "org-id",
        "base_url": "custom-endpoint"
    }
)

provider = await create_provider(**config.dict())
```

## Async Context Manager

Providers can be used as async context managers for automatic cleanup:

```python
async with await create_provider("openai", api_key="...") as provider:
    response = await provider.complete("Hello!")
    # Resources automatically cleaned up after context exit
```

## Streaming Responses

All providers support streaming responses for real-time output:

```python
async def process_stream():
    provider = await create_provider("openai", api_key="...")
    
    async for chunk in await provider.complete(
        "Generate a story...",
        stream=True,
        temperature=0.7
    ):
        print(chunk, end="", flush=True)
        # Process chunks as they arrive
```

## Embeddings Generation

Generate embeddings for semantic search and similarity:

```python
async def generate_embeddings():
    provider = await create_provider("openai", api_key="...")
    
    # Single text embedding
    embeddings = await provider.embed("Text to embed")
    
    # Custom embedding model (provider-specific)
    embeddings = await provider.embed(
        "Text to embed",
        model="text-embedding-3-large"
    )
```

## Error Handling

The provider system includes comprehensive error handling:

```python
from pepperpy.providers.domain import (
    ProviderError,
    ProviderAPIError,
    ProviderRateLimitError
)

async def handle_errors():
    try:
        provider = await create_provider("openai", api_key="...")
        response = await provider.complete("Hello!")
        
    except ProviderRateLimitError as e:
        print(f"Rate limit exceeded: {e}")
        print(f"Provider: {e.provider_type}")
        print(f"Details: {e.details}")
        # Handle rate limiting (e.g., implement backoff)
        
    except ProviderAPIError as e:
        print(f"API error: {e}")
        print(f"Provider: {e.provider_type}")
        print(f"Details: {e.details}")
        # Handle API errors
        
    except ProviderError as e:
        print(f"Provider error: {e}")
        # Handle other provider errors
```

## Best Practices

1. **Configuration Management**
   ```python
   # Use environment variables for API keys
   import os
   from pepperpy.providers import create_provider
   
   provider = await create_provider(
       "openai",
       api_key=os.getenv("OPENAI_API_KEY")
   )
   ```

2. **Resource Cleanup**
   ```python
   # Always use async context manager or cleanup
   async with await create_provider("openai", api_key="...") as provider:
       # Use provider
       pass  # Automatically cleaned up
   
   # Or manually cleanup
   provider = await create_provider("openai", api_key="...")
   try:
       # Use provider
       pass
   finally:
       await provider.cleanup()
   ```

3. **Error Handling**
   ```python
   # Implement proper error handling and retries
   from pepperpy.providers.domain import ProviderRateLimitError
   import asyncio
   
   async def with_retries(prompt: str, max_retries: int = 3):
       for attempt in range(max_retries):
           try:
               provider = await create_provider("openai", api_key="...")
               return await provider.complete(prompt)
           except ProviderRateLimitError:
               if attempt == max_retries - 1:
                   raise
               await asyncio.sleep(2 ** attempt)  # Exponential backoff
   ```

4. **Streaming Best Practices**
   ```python
   # Implement proper stream handling
   async def handle_stream():
       provider = await create_provider("openai", api_key="...")
       buffer = []
       
       async for chunk in await provider.complete(
           "Generate...",
           stream=True
       ):
           buffer.append(chunk)
           # Process in chunks for efficiency
           if len(buffer) >= 10:
               await process_chunks(buffer)
               buffer.clear()
       
       # Process remaining chunks
       if buffer:
           await process_chunks(buffer)
   ```

## Advanced Usage

### Custom Provider Implementation

Create custom providers by implementing the `Provider` interface:

```python
from pepperpy.providers import Provider, ProviderConfig
from typing import Optional, Union, AsyncIterator, Any

class CustomProvider(Provider):
    """Custom provider implementation."""
    
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client = None
    
    async def initialize(self) -> None:
        """Initialize provider resources."""
        # Setup your client/resources
        await super().initialize()
    
    async def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> Union[str, AsyncIterator[str]]:
        """Implement completion logic."""
        self._check_initialized()
        # Implement your completion logic
        pass
    
    async def embed(
        self,
        text: str,
        **kwargs: Any
    ) -> list[float]:
        """Implement embedding logic."""
        self._check_initialized()
        # Implement your embedding logic
        pass
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Cleanup your resources
        await super().cleanup()
```

### Provider Registry

Register custom providers with the provider engine:

```python
from pepperpy.providers.engine import ProviderEngine

# Register your provider
ProviderEngine.register_provider("custom", CustomProvider)

# List available providers
providers = ProviderEngine.list_providers()
print(f"Available providers: {providers}")

# Create instance of your provider
provider = await create_provider("custom", api_key="...")
```

## Environment Variables

Providers support configuration through environment variables:

```bash
# OpenAI
export PEPPERPY_PROVIDER_OPENAI_API_KEY="your-openai-key"
export PEPPERPY_PROVIDER_OPENAI_MODEL="gpt-4"

# Gemini
export PEPPERPY_PROVIDER_GEMINI_API_KEY="your-gemini-key"
export PEPPERPY_PROVIDER_GEMINI_MODEL="gemini-pro"

# OpenRouter
export PEPPERPY_PROVIDER_OPENROUTER_API_KEY="your-openrouter-key"
export PEPPERPY_PROVIDER_OPENROUTER_MODEL="openai/gpt-4"

# StackSpot
export PEPPERPY_PROVIDER_STACKSPOT_API_KEY="your-stackspot-key"
export PEPPERPY_PROVIDER_STACKSPOT_MODEL="gpt-4"
```

Then in your code:

```python
# Configuration will be loaded from environment
provider = await create_provider("openai")
```

## Performance Considerations

1. **Connection Pooling**
   - Providers maintain connection pools for efficiency
   - Reuse provider instances when possible
   - Clean up resources when done

2. **Streaming Efficiency**
   - Use streaming for long responses
   - Process chunks efficiently
   - Implement proper backpressure

3. **Resource Management**
   - Use async context managers
   - Implement proper cleanup
   - Monitor resource usage

4. **Error Handling**
   - Implement proper retries
   - Use exponential backoff
   - Handle rate limits appropriately

## Security Considerations

1. **API Key Management**
   - Never hardcode API keys
   - Use environment variables
   - Implement proper key rotation

2. **Error Handling**
   - Don't expose internal errors
   - Implement proper logging
   - Monitor for security issues

3. **Input Validation**
   - Validate all inputs
   - Implement proper sanitization
   - Monitor for abuse

4. **Rate Limiting**
   - Implement proper rate limiting
   - Monitor usage patterns
   - Implement proper quotas 