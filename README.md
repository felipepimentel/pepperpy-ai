# Pepperpy Provider System

A unified, provider-agnostic interface for interacting with various AI services.

## Features

- Clean, provider-agnostic API
- Type-safe implementation
- Async/await support
- Streaming support
- Environment-based configuration
- Comprehensive error handling
- Rate limiting support

## Supported Providers

- OpenAI
- StackSpotAI (coming soon)
- OpenRouter (coming soon)
- Gemini (coming soon)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from pepperpy.providers import create_provider

# Create a provider (using environment variable PEPPERPY_PROVIDER_OPENAI_API_KEY)
async with create_provider("openai") as provider:
    response = await provider.complete(
        "Translate to Portuguese: Hello, world!",
        temperature=0.7
    )
    print(response)  # Olá, mundo!

# Or with explicit API key
provider = create_provider("openai", api_key="your-api-key")
await provider.initialize()
try:
    response = await provider.complete("Hello!")
    print(response)
finally:
    await provider.cleanup()
```

### Streaming Responses

```python
async with create_provider("openai") as provider:
    async for chunk in await provider.complete(
        "Tell me a story",
        stream=True
    ):
        print(chunk, end="", flush=True)
```

### Embeddings

```python
async with create_provider("openai") as provider:
    embedding = await provider.embed("Hello, world!")
    print(f"Embedding dimension: {len(embedding)}")
```

### Environment Configuration

```bash
# Provider API keys
export PEPPERPY_PROVIDER_OPENAI_API_KEY="sk-..."
export PEPPERPY_PROVIDER_GEMINI_API_KEY="..."

# Optional provider configuration
export PEPPERPY_PROVIDER_OPENAI_MODEL="gpt-4"
export PEPPERPY_PROVIDER_TIMEOUT="60.0"
```

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Type checking
mypy .

# Format code
black .
isort .
```

### Adding a New Provider

1. Create provider implementation in `pepperpy/providers/services/`
2. Implement the `Provider` protocol
3. Register provider in `pepperpy/providers/services/__init__.py`

Example:

```python
from pepperpy.providers import Provider, ProviderConfig

class MyProvider(Provider):
    async def initialize(self) -> None:
        # Setup provider
        await super().initialize()
    
    async def complete(self, prompt: str, **kwargs) -> str:
        # Implement completion
        return "Response"
    
    async def embed(self, text: str, **kwargs) -> list[float]:
        # Implement embedding
        return [0.1, 0.2, 0.3]
```

## License

MIT
