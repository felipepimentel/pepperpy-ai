# PepperPy

A flexible and extensible Python framework for AI applications.

## Features

- 🚀 Simple and intuitive API
- 🔌 Plugin-based architecture for providers
- 🎯 Focused on developer experience
- 🛠️ Easy to extend and customize
- 🔄 Async-first design

## Installation

```bash
pip install pepperpy
```

## Quick Start

Here's a simple example using the OpenAI provider:

```python
import asyncio
import os
from pepperpy import PepperPy

async def main():
    # Create a PepperPy instance with the OpenAI provider
    async with PepperPy().with_llm(
        provider_type="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-3.5-turbo"
    ) as pepper:
        # Use the fluent API to generate text
        result = await (
            pepper.chat
            .with_system("You are a helpful assistant.")
            .with_user("Tell me about Python.")
            .generate()
        )
        
        print(f"Assistant: {result.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Streaming Support

PepperPy supports streaming responses:

```python
async def stream_example():
    async with PepperPy().with_llm(
        provider_type="openai",
        api_key=os.environ.get("OPENAI_API_KEY")
    ) as pepper:
        print("Assistant: ", end="", flush=True)
        
        # Stream the response
        stream = await (
            pepper.chat
            .with_user("Tell me a story.")
            .generate_stream()
        )
        
        async for chunk in stream:
            print(chunk.content, end="", flush=True)
        print()  # New line at the end
```

## Available Providers

### LLM Providers

- OpenAI (`provider_type="openai"`)
  - Requires: `OPENAI_API_KEY`
  - Models: `gpt-3.5-turbo`, `gpt-4`, etc.

More providers coming soon!

## Development

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pepperpy.git
cd pepperpy
```

2. Install dependencies:
```bash
poetry install
```

3. Run tests:
```bash
poetry run pytest
```

### Creating a Provider Plugin

1. Create a new directory in `plugins/`:
```bash
mkdir -p plugins/llm_myprovider
```

2. Create the required files:
- `plugin.json`: Plugin metadata
- `provider.py`: Provider implementation
- `requirements.txt`: Provider dependencies

Example `plugin.json`:
```json
{
  "name": "llm_myprovider",
  "version": "1.0.0",
  "category": "llm",
  "provider_name": "myprovider",
  "description": "My custom provider for PepperPy",
  "entry_point": "provider:MyProvider"
}
```

Example `provider.py`:
```python
from pepperpy.llm import LLMProvider, Message, GenerationResult

class MyProvider(LLMProvider):
    name = "myprovider"
    
    async def generate(self, messages, **kwargs):
        # Implement generation logic
        pass
    
    async def generate_stream(self, messages, **kwargs):
        # Implement streaming logic
        pass
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 