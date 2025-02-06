# Pepperpy Framework

Pepperpy is a powerful framework for building AI agents with modular components, extensible providers, and robust memory management.

## Features

- **Modular Architecture**: Build agents using composable components
- **Multiple Providers**: Support for OpenAI, Anthropic, and more
- **Memory Management**: Redis and vector store support for persistent memory
- **Framework Adapters**: Integrate with LangChain, AutoGen, and other frameworks
- **Type Safety**: Full type hints and runtime validation
- **Async Support**: Built for high-performance async operations
- **Observability**: Comprehensive logging, metrics, and tracing

## Installation

```bash
# Install from PyPI
pip install pepperpy

# Install with all extras
pip install pepperpy[all]

# Install specific extras
pip install pepperpy[redis,vector,monitoring]
```

## Quick Start

```python
from pepperpy.core import Message
from pepperpy.providers import OpenAIProvider
from pepperpy.memory import RedisMemoryStore

# Configure provider
provider = OpenAIProvider(
    config=OpenAIConfig(
        model="gpt-4",
        api_key="your-api-key",
    )
)

# Configure memory store
memory = RedisMemoryStore(
    config=RedisConfig(
        host="localhost",
        port=6379,
    )
)

# Initialize components
await provider.initialize()
await memory.initialize()

# Process messages
message = Message(
    sender="user",
    content={"query": "What's the weather?"},
)

response = await provider.generate([message])
await memory.add_to_conversation("chat-1", message)
```

## Development

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pepperpy.git
   cd pepperpy
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r tests/requirements.txt
   ```

### Testing

Run tests with pytest:
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m "not slow"        # Skip slow tests
pytest -m integration       # Run integration tests
pytest -m "memory or redis" # Run memory-related tests

# Run with coverage
pytest --cov=pepperpy

# Run in parallel
pytest -n auto
```

### Code Quality

1. Type checking:
   ```bash
   mypy pepperpy tests
   ```

2. Linting:
   ```bash
   ruff check pepperpy tests
   ```

3. Code formatting:
   ```bash
   ruff format pepperpy tests
   ```

## Project Structure

```
pepperpy/
├── core/               # Core framework components
│   ├── base.py        # Base classes and interfaces
│   ├── config.py      # Configuration management
│   ├── errors.py      # Error definitions
│   ├── events.py      # Event system
│   ├── registry.py    # Component registry
│   ├── types.py       # Core type definitions
│   └── utils.py       # Utility functions
│
├── providers/         # Model providers
│   ├── base.py       # Provider interface
│   ├── openai.py     # OpenAI provider
│   └── anthropic.py  # Anthropic provider
│
├── memory/           # Memory management
│   ├── base.py      # Memory store interface
│   ├── manager.py   # Memory manager
│   └── storage/     # Store implementations
│       ├── redis.py # Redis store
│       └── vector.py # Vector store
│
├── adapters/         # Framework adapters
│   ├── base.py      # Adapter interface
│   ├── errors.py    # Adapter errors
│   └── frameworks/  # Framework implementations
│       ├── langchain.py
│       ├── autogen.py
│       └── crewai.py
│
└── monitoring/      # Observability
    ├── logger.py   # Logging configuration
    ├── metrics.py  # Metrics collection
    └── tracing.py  # Distributed tracing
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development process.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
