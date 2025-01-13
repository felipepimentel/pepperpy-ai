# PepperPy AI

A flexible AI library with modular provider support.

## Installation

PepperPy AI uses a modular dependency system to keep the base package lightweight. You only need to install the dependencies for the features you plan to use.

### Basic Installation

```bash
# Using pip
pip install pepperpy-ai

# Using Poetry
poetry add pepperpy-ai
```

### Optional Features

Install only what you need:

```bash
# OpenAI support
pip install pepperpy-ai[openai]
poetry add pepperpy-ai[openai]

# Anthropic support
pip install pepperpy-ai[anthropic]
poetry add pepperpy-ai[anthropic]

# RAG (Retrieval Augmented Generation) support
pip install pepperpy-ai[rag]
poetry add pepperpy-ai[rag]

# All providers
pip install pepperpy-ai[all-providers]
poetry add pepperpy-ai[all-providers]

# All capabilities
pip install pepperpy-ai[all-capabilities]
poetry add pepperpy-ai[all-capabilities]

# Everything
pip install pepperpy-ai[complete]
poetry add pepperpy-ai[complete]
```

## Development Setup

For development, you'll need additional dependencies. We use Poetry groups to manage these:

```bash
# Clone the repository
git clone https://github.com/pimentel/pepperpy-ai.git
cd pepperpy-ai

# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install with development dependencies
poetry install --with dev,test,docs

# Run tests
poetry run pytest

# Run linters
poetry run ruff check .
poetry run mypy .

# Format code
poetry run black .
poetry run isort .
```

## Project Structure

The project uses a modular dependency system:

- **Core Dependencies**: Minimal set of required packages
- **Optional Features**: Additional capabilities through extras
- **Development Tools**: Linting, formatting, and testing (dev group)
- **Test Framework**: Testing tools and dependencies (test group)
- **Documentation**: Documentation building tools (docs group)

This structure ensures that users only install what they need, while developers have access to all necessary tools.

## Contributing

1. Fork the repository
2. Install development dependencies: `poetry install --with dev,test,docs`
3. Create a feature branch
4. Make your changes
5. Run tests and linters
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
