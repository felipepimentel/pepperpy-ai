# PepperPy OpenAI Provider

OpenAI provider implementation for PepperPy.

## Installation

```bash
pip install pepperpy-llm-openai
```

## Usage

```python
from pepperpy import PepperPy

# Using environment variables (recommended)
async with PepperPy().with_llm(provider_type="openai") as pepper:
    result = await pepper.chat.with_user("Hello!").generate()
    print(result.content)

# Or with explicit configuration
async with PepperPy().with_llm(
    provider_type="openai",
    api_key="your-api-key",
    model="gpt-3.5-turbo",
    temperature=0.7,
) as pepper:
    result = await pepper.chat.with_user("Hello!").generate()
    print(result.content)
```

## Configuration

The provider accepts the following configuration options:

- `api_key`: OpenAI API key (required)
- `model`: Model to use (default: "gpt-3.5-turbo")
- `temperature`: Sampling temperature (default: 0.7)
- `max_tokens`: Maximum tokens to generate (optional)

All configuration options can be set via environment variables (recommended) or passed directly to the constructor.

## Environment Variables

The provider will automatically use these environment variables if set:

### Primary Variables
- `OPENAI_API_KEY`: OpenAI API key (standard OpenAI environment variable)

### PepperPy-specific Variables
- `PEPPERPY_LLM__OPENAI__API_KEY`: Alternative API key location
- `PEPPERPY_LLM__OPENAI__MODEL`: Model to use (default: "gpt-3.5-turbo")
- `PEPPERPY_LLM__OPENAI__TEMPERATURE`: Sampling temperature (default: 0.7)
- `PEPPERPY_LLM__OPENAI__MAX_TOKENS`: Maximum tokens to generate

Environment variables take precedence in this order:
1. Constructor parameters
2. PepperPy-specific variables
3. Standard OpenAI variables
4. Default values

## Features

- Full support for OpenAI's chat completion API
- Streaming support
- Token usage tracking
- Proper error handling and validation
- Automatic resource cleanup
- Smart environment variable configuration

## Examples

### Using Environment Variables

```bash
# Set up environment variables
export PEPPERPY_LLM__OPENAI__API_KEY="your-api-key"
export PEPPERPY_LLM__OPENAI__MODEL="gpt-4"
export PEPPERPY_LLM__OPENAI__TEMPERATURE="0.8"
export PEPPERPY_LLM__OPENAI__MAX_TOKENS="2000"

# Run your code
python your_script.py
```

### Streaming Example

```python
async with PepperPy().with_llm(provider_type="openai") as pepper:
    async for chunk in await (
        pepper.chat
        .with_system("You are a creative storyteller.")
        .with_user("Tell me a story about a magical forest.")
        .stream()
    ):
        print(chunk.content, end="", flush=True)
```

## Error Handling

The provider includes proper error handling and validation:

- Validates API key presence
- Checks for valid configuration values
- Provides clear error messages
- Handles API errors gracefully

## License

MIT License 