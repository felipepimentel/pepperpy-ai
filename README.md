# PepperPy AI

A flexible AI library with modular provider support.

## Features

- Multiple AI provider support (OpenAI, Anthropic, StackSpot, OpenRouter)
- Modular capabilities (RAG, Chat, Embeddings)
- Plug-and-play architecture
- Async-first design
- Type-safe with comprehensive type hints
- Extensive test coverage
- Well-documented API

## Installation

You can install PepperPy AI with pip:

```bash
pip install pepperpy-ai
```

### Optional Dependencies

PepperPy AI uses Poetry's extras feature to manage optional dependencies. You can install specific providers or capabilities:

```bash
# Install with OpenAI support
pip install "pepperpy-ai[openai]"

# Install with Anthropic support
pip install "pepperpy-ai[anthropic]"

# Install with RAG support
pip install "pepperpy-ai[rag]"

# Install with all capabilities
pip install "pepperpy-ai[all-capabilities]"

# Install with all providers
pip install "pepperpy-ai[all-providers]"

# Install complete package with all features
pip install "pepperpy-ai[complete]"
```

## Usage

Here's a simple example using the OpenAI provider:

```python
from pepperpy_ai import AIClient
from pepperpy_ai.providers import OpenAIProvider

# Initialize the client with OpenAI provider
client = AIClient(
    provider=OpenAIProvider(
        api_key="your-api-key",
        model="gpt-4-turbo-preview"
    )
)

# Use the chat capability
chat = await client.get_capability("chat")
response = await chat.send_message("Hello, how are you?")
print(response.content)
```

Using RAG capabilities:

```python
from pepperpy_ai import AIClient
from pepperpy_ai.providers import OpenAIProvider
from pepperpy_ai.capabilities.rag import Document

# Initialize the client
client = AIClient(
    provider=OpenAIProvider(
        api_key="your-api-key",
        model="gpt-4-turbo-preview"
    )
)

# Get RAG capability
rag = await client.get_capability("rag")

# Add documents
docs = [
    Document(
        content="PepperPy is a flexible AI library.",
        metadata={"source": "readme"}
    ),
    Document(
        content="It supports multiple AI providers.",
        metadata={"source": "docs"}
    )
]
await rag.add_documents(docs)

# Generate response with context
response = await rag.generate("What is PepperPy?")
print(response.content)
```

## Development

### Setup

1. Clone the repository:
```bash
git clone https://github.com/pimentel/pepperpy-ai.git
cd pepperpy-ai
```

2. Install development environment:
```bash
./scripts/setup.sh
```

3. Activate virtual environment:
```bash
poetry shell
```

### Quality Checks

Run all quality checks:
```bash
./scripts/check.sh
```

This includes:
- Code formatting (black, isort)
- Linting (ruff)
- Type checking (mypy)
- Security checks (bandit)
- Tests (pytest)

### Clean

Remove temporary files and build artifacts:
```bash
./scripts/clean.sh
```

### Publishing

To publish a new version:
```bash
./scripts/publish.sh VERSION
```

Replace `VERSION` with the new version number (e.g., `1.0.0`).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run quality checks
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
