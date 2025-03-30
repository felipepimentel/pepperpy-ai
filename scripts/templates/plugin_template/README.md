# Template Provider

A template provider for DOMAIN tasks in the PepperPy framework.

## Features

- Implements the DOMAIN provider interface
- Follows all PepperPy plugin best practices
- [Add specific features here]

## Requirements

- PepperPy framework (>=0.1.0)
- API key for the service

## Installation

This plugin is included in the PepperPy framework. No additional installation is needed.

## Configuration

Set up your configuration using any of these methods:

1. Pass configuration when creating the provider:
   ```python
   from pepperpy import create_provider
   
   provider = create_provider("domain", "template", 
                              api_key="your-api-key",
                              model="custom-model")
   ```

2. Use environment variables:
   ```
   TEMPLATE_API_KEY=your-api-key
   PEPPERPY_DOMAIN__TEMPLATE__MODEL=custom-model
   ```

## Usage

```python
from pepperpy import create_provider

# Create the provider
provider = create_provider("domain", "template", api_key="your-api-key")

# Initialize (done automatically when needed)
await provider.initialize()

# Use domain-specific methods
result = await provider.domain_method("input data")

# Clean up when done
await provider.cleanup()
```

## Configuration Options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `api_key` | API key for authentication | Yes | - |
| `base_url` | API base URL | No | `https://api.example.com/v1` |
| `model` | Model to use | No | `default-model` |
| `temperature` | Sampling temperature | No | `0.7` |
| `max_tokens` | Maximum tokens to generate | No | `1024` |

## License

This plugin is part of the PepperPy framework and is licensed under the same terms. 