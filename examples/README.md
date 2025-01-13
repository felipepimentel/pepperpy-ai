# PepperPy AI Examples

This directory contains example scripts demonstrating how to use PepperPy AI in various scenarios.

## Running Examples

Before running any example, make sure you have installed PepperPy AI with the required dependencies for that example.
Each example may require different optional dependencies, which can be installed using Poetry extras.

### Basic Chat Example

The basic chat example (`basic_chat.py`) demonstrates how to use AI providers for chat interactions.
By default, it uses OpenRouter as the provider, but you can easily switch to other providers using environment variables.

Required dependencies:

Using pip:
```bash
# Install with OpenRouter support (recommended)
pip install pepperpy-ai[openrouter]

# Or install other providers
pip install pepperpy-ai[openai]      # For OpenAI
pip install pepperpy-ai[anthropic]   # For Anthropic
pip install pepperpy-ai[all-providers]  # For all providers
```

Using Poetry:
```bash
# Install with OpenRouter support (recommended)
poetry add pepperpy-ai[openrouter]

# Or install other providers
poetry add pepperpy-ai[openai]      # For OpenAI
poetry add pepperpy-ai[anthropic]   # For Anthropic
poetry add pepperpy-ai[all-providers]  # For all providers
```

Environment variables:
```bash
# Required
export PEPPERPY_API_KEY="your-api-key"

# Optional (defaults shown)
export PEPPERPY_PROVIDER="openrouter"  # openai, anthropic, openrouter, mock
export PEPPERPY_MODEL="anthropic/claude-2"  # provider-specific model
export PEPPERPY_TEMPERATURE="0.7"
export PEPPERPY_MAX_TOKENS="1000"
export PEPPERPY_TIMEOUT="30.0"
```

Provider-specific defaults:
- OpenRouter: `anthropic/claude-2`
- OpenAI: `gpt-3.5-turbo`
- Anthropic: `claude-2.1`

Run the example:
```bash
# Using Python directly
python examples/basic_chat.py

# Using Poetry
poetry run python examples/basic_chat.py
```

### Error Handling

The examples demonstrate proper error handling, including helpful messages when:
- Dependencies are missing
- API key is not set or invalid
- Provider configuration is incorrect
- Network errors occur

If you see an error, follow the instructions provided in the error message.

## Available Examples

1. `basic_chat.py` - Simple chat interaction using configurable AI providers
2. (More examples coming soon)

## Best Practices

- Always handle dependency errors using try/except blocks
- Use environment variables for configuration
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
