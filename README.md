# PepperPy Framework

PepperPy is a Python framework for building AI-powered applications. It provides tools and utilities for composing pipelines, processing data, and integrating with AI services.

## Features

- **Pipeline Composition**: Build data processing pipelines with a fluent interface
- **Intent Recognition**: Extract user intents from natural language
- **RAG Support**: Build Retrieval Augmented Generation applications
- **Workflow Management**: Orchestrate complex tasks and workflows
- **Type Safety**: Full type hints and runtime type checking
- **Extensible**: Easy to extend with custom components

## Installation

```bash
pip install pepperpy
```

Or with Poetry:

```bash
poetry add pepperpy
```

## Quick Start

Here's a simple example of using PepperPy to build a pipeline:

```python
from pepperpy.core import compose, Sources, Processors, Outputs

# Create a pipeline
pipeline = compose("example")

# Add stages
pipeline.source(Sources.text("hello"))
pipeline.process(Processors.transform(str.upper))
pipeline.output(Outputs.console())

# Execute pipeline
await pipeline.execute()  # Prints: HELLO
```

And here's an example of using intent recognition:

```python
from pepperpy.core import recognize_intent

# Recognize intent from text
intent = await recognize_intent("traduzir hello world")
assert intent.name == "translate"
assert intent.entities["text"] == "hello world"
```

## Documentation

For more examples and detailed documentation, see:

- [User Guide](docs/guide.md)
- [API Reference](docs/api.md)
- [Examples](examples/)

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/pepperpy.git
cd pepperpy

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linters
poetry run black .
poetry run isort .
poetry run mypy .
poetry run ruff check .
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 

