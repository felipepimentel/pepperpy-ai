# PepperPy AI Examples

This directory contains example scripts demonstrating how to use PepperPy AI in various scenarios.

## Running Examples

Before running any example, make sure you have installed PepperPy AI with the required dependencies for that example.
Each example may require different optional dependencies, which can be installed using Poetry extras.

### Basic Chat Example

The basic chat example (`basic_chat.py`) demonstrates how to use the OpenAI provider for a simple chat interaction.

Required dependencies:

Using pip:
```bash
# Install with OpenAI provider support
pip install pepperpy-ai[openai]

# Or install all providers
pip install pepperpy-ai[all-providers]
```

Using Poetry:
```bash
# Install with OpenAI provider support
poetry add pepperpy-ai[openai]

# Or install all providers
poetry add pepperpy-ai[all-providers]
```

Environment variables:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Run the example:
```bash
# Using Python directly
python examples/basic_chat.py

# Using Poetry
poetry run python examples/basic_chat.py
```

### Error Handling

The examples demonstrate proper error handling, including helpful messages when optional dependencies are missing.
If you see an error about missing dependencies, follow the installation instructions provided in the error message.

## Available Examples

1. `basic_chat.py` - Simple chat interaction using OpenAI's GPT models
2. (More examples coming soon)

## Best Practices

- Always handle dependency errors using try/except blocks
- Use environment variables for API keys
- Clean up resources using finally blocks
- Use type hints for better code safety
- Follow async/await patterns for I/O operations
- Use Poetry for dependency management
- Install only the dependencies you need using extras

## Contributing

Feel free to contribute more examples by submitting a pull request. Make sure your examples:

1. Follow the project's code style
2. Include proper error handling
3. Demonstrate best practices
4. Are well documented
5. Include type hints
6. Use appropriate Poetry extras for dependencies
