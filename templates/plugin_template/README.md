# Domain Provider Plugin

This plugin provides [brief description of functionality].

## Features

- Feature 1
- Feature 2
- Feature 3

## Configuration

The plugin accepts the following configuration options:

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `option1` | string | Description of option1 | `"default_value"` |
| `option2` | integer | Description of option2 | `42` |
| `array_option` | array | List of values | `["value1", "value2"]` |

## Usage

### Basic Example

```python
from pepperpy import PepperPy

# Initialize PepperPy with this plugin
pepperpy = PepperPy().with_domain("provider", option1="custom_value")

# Use the plugin
result = await pepperpy.domain.process("input data")
print(result)
```

### Advanced Example

```python
# Custom configuration
config = {
    "option1": "custom_value",
    "option2": 100,
    "array_option": ["custom1", "custom2"]
}

# Initialize with custom configuration
pepperpy = PepperPy().with_domain("provider", **config)

# Execute a specific task
result = await pepperpy.execute({
    "plugin": "domain/provider",
    "task": "specific_task",
    "data": {
        "key": "value"
    }
})
```

## Direct Access (Development Only)

For development or debugging purposes only, you can access the provider directly:

```python
from plugins.domain.category.provider import ProviderClass

# Create instance
provider = ProviderClass(option1="custom_value")

# Initialize
await provider.initialize()

try:
    # Execute task
    result = await provider.execute({
        "task": "specific_task",
        "param1": "value1"
    })
    print(result)
finally:
    # Clean up resources
    await provider.cleanup()
```

## Testing

Test the plugin with the included examples:

```bash
python -m pepperpy.plugin.test plugins/domain/category/provider
```

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt` 