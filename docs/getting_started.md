# Getting Started with PepperPy AI

This guide will help you get started with PepperPy AI, from installation to basic usage.

## Installation

PepperPy AI can be installed using Poetry:

```bash
poetry add pepperpy-ai
```

To install with all optional dependencies:

```bash
poetry add "pepperpy-ai[providers]"
```

## Quick Start

Here's a simple example to get you started:

```python
from pepperpy_ai.client import PepperPyAI
from pepperpy_ai.config import Config

async def main():
    # Initialize the client
    config = Config()
    client = PepperPyAI(config)
    
    # Use the client
    result = await client.process_request("Your request here")
    print(result)

```

## Basic Configuration

PepperPy AI can be configured through environment variables or programmatically:

```python
from pepperpy_ai.config import Config

config = Config(
    provider="openai",  # or "anthropic"
    api_key="your-api-key",
    cache_enabled=True,
)
```

### Environment Variables

- `PEPPERPY_PROVIDER`: The AI provider to use
- `PEPPERPY_API_KEY`: Your API key
- `PEPPERPY_CACHE_ENABLED`: Enable/disable caching

## Next Steps

- Explore the [Core Concepts](./core_concepts.md) to understand the architecture
- Check out the [Examples](./examples/index.md) for more use cases
- Read the [API Reference](./api_reference/index.md) for detailed information 