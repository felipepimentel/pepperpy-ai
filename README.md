# Pepperpy

A powerful AI agent framework for building intelligent applications.

## Features

- 🤖 Agent-based architecture
- 🔄 Event-driven communication
- 🔌 Provider abstraction (LLM, Storage, Memory)
- 📝 Content synthesis
- 🔄 Workflow management
- 📊 Monitoring and metrics
- 🔒 Security and validation

## Requirements

- Python 3.12 or higher
- Poetry (recommended) or pip
- Redis (optional, for memory provider)
- PostgreSQL (optional, for memory provider)

## Installation

### Using Poetry (Recommended)

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/yourusername/pepperpy.git
cd pepperpy

# Install dependencies
poetry install

# Install specific extras
poetry install --extras "llm"  # For LLM support
poetry install --extras "storage"  # For storage support
poetry install --extras "memory"  # For memory support
```

### Using pip

```bash
# Install from PyPI
pip install pepperpy

# Install with extras
pip install pepperpy[llm]  # For LLM support
pip install pepperpy[storage]  # For storage support
pip install pepperpy[memory]  # For memory support
pip install pepperpy[all]  # Install all extras
```

## Quick Start

1. Set up your environment:
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
poetry install  # or: pip install -r requirements.txt
```

2. Set required environment variables:
```bash
# For OpenAI provider
export PEPPERPY_OPENAI_API_KEY=your_api_key

# For Anthropic provider
export PEPPERPY_ANTHROPIC_API_KEY=your_api_key

# For Redis memory provider
export PEPPERPY_REDIS_URL=redis://localhost:6379
```

3. Run an example:
```bash
# Run the quickstart example
python examples/quickstart.py

# Run with test mode
python examples/quickstart.py --test
```

## Examples

The `examples/` directory contains several examples demonstrating different features:

- `quickstart.py`: Basic task assistant
- `content_example.py`: Content module functionality
- `research_agent.py`: Research workflow
- `news_podcast.py`: News-to-podcast generation
- `personal_assistant.py`: Personal assistant features
- `story_creation.py`: Story generation
- `collaborative_research.py`: Multi-agent research
- `hub_integration.py`: Hub system integration

Each example includes detailed comments and demonstrates proper:
- Resource initialization
- Error handling
- Resource cleanup
- Configuration management
- Logging

## Development

1. Set up development environment:
```bash
# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
pre-commit install
```

2. Run tests:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pepperpy

# Run specific test file
pytest tests/test_specific.py
```

3. Run code quality checks:
```bash
# Run all checks
./scripts/check.sh

# Run specific checks
black pepperpy/
isort pepperpy/
mypy pepperpy/
```

4. Clean up:
```bash
# Clean temporary files
./scripts/clean.sh

# Clean including virtual environment
./scripts/clean.sh --venv
```

## Documentation

Build the documentation:
```bash
# Install documentation dependencies
poetry install --with docs

# Build documentation
cd docs
make html
```

View the documentation at `docs/_build/html/index.html`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and checks
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
