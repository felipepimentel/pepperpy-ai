# PepperPy AI

A flexible and modular AI library that supports multiple providers and capabilities.

## Installation

PepperPy AI uses Poetry for dependency management and provides several installation options to minimize dependencies based on your needs.

### Basic Installation

```bash
# Basic installation with core functionality
poetry add pepperpy-ai
```

### Provider-Specific Installation

Install only the providers you need:

```bash
# OpenAI support
poetry add "pepperpy-ai[openai]"

# Anthropic support
poetry add "pepperpy-ai[anthropic]"

# StackSpot support (uses core HTTP client)
poetry add "pepperpy-ai[stackspot]"

# OpenRouter support (uses core HTTP client)
poetry add "pepperpy-ai[openrouter]"

# All providers
poetry add "pepperpy-ai[all-providers]"
```

### Additional Capabilities

```bash
# Embedding support (sentence-transformers)
poetry add "pepperpy-ai[embeddings]"

# Enhanced resilience (retries, backoff)
poetry add "pepperpy-ai[resilience]"
```

### Complete Installation

For all features and providers:

```bash
poetry add "pepperpy-ai[complete]"
```

## Available Extras

The package provides the following extras for optional dependencies:

- `openai`: OpenAI API support
- `anthropic`: Anthropic API support
- `stackspot`: StackSpot API support
- `openrouter`: OpenRouter API support
- `embeddings`: Text embedding capabilities
- `resilience`: Enhanced error handling and retries
- `all-providers`: All supported AI providers
- `complete`: All features and providers

## Usage Examples

### Basic Usage with OpenAI

```python
from pepperpy_ai.providers import OpenAIProvider
from pepperpy_ai.llm.config import LLMConfig

config = LLMConfig(
    provider="openai",
    model="gpt-4",
    api_key="your-api-key"
)

async with OpenAIProvider(config) as provider:
    response = await provider.complete("Hello, world!")
    print(response.content)
```

### Using Embeddings

```python
from pepperpy_ai.embeddings import SentenceTransformerEmbeddings

embeddings = SentenceTransformerEmbeddings()
vectors = await embeddings.embed_texts(["Hello, world!"])
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/pepperpy-ai.git
cd pepperpy-ai

# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest
```

## License

MIT License - see LICENSE file for details.
