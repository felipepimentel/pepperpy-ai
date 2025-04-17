# PepperPy OpenAI LLM Provider

This plugin provides OpenAI language model integration for the PepperPy framework.

## Features

- Chat completions
- Text completions
- Streaming responses
- Embedding generation

## Installation

```bash
pip install pepperpy-llm-openai
```

## Usage

```python
from pepperpy import PepperPy
from pepperpy.llm import Message

# Initialize PepperPy with OpenAI
pepper = PepperPy().with_llm("openai", api_key="your_api_key")
await pepper.initialize()

# Create messages
messages = [
    Message(role="system", content="You are a helpful assistant."),
    Message(role="user", content="Hello, how are you?")
]

# Get a response
response = await pepper.llm.chat(messages)
print(response)

# Stream a response
async for chunk in pepper.llm.stream_chat(messages):
    print(chunk, end="", flush=True)

# Generate embeddings
embedding = await pepper.llm.embed("This is a text to embed")
```

## Configuration

The plugin accepts the following configuration options:

- `api_key`: OpenAI API key (required)
- `model`: Model name (default: "gpt-3.5-turbo")
- `organization`: OpenAI organization ID (optional)

## Requirements

- Python 3.10+
- openai >= 1.0.0 