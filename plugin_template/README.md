# Template PepperPy Plugin

This is a template plugin for PepperPy that follows the implementation guide. Use this template as a starting point for creating new plugins.

## Structure

- `provider.py` - The provider implementation
- `plugin.yaml` - Plugin metadata and configuration
- `README.md` - Documentation

## Implementation Details

This template demonstrates the correct implementation pattern for PepperPy plugins:

1. **Class Inheritance**
   - Inherits from both domain interface and `BasePluginProvider`
   - Properly implements `initialize()` and `cleanup()`

2. **Configuration Management**
   - Uses `self.config.get()` for accessing configuration
   - No hardcoded configuration values in the provider class

3. **Resource Management**
   - Initializes resources in `initialize()`, not in `__init__()`
   - Properly cleans up resources in `cleanup()`

4. **Error Handling**
   - Properly handles and logs errors
   - Converts external errors to domain-specific errors

## Usage

```python
from pepperpy import PepperPy

app = PepperPy.create().with_domain("template").build()

result = await app.domain.execute({
    "task": "task_one",
    "param": "my_value"
})

print(result)
```

## Testing

```bash
# Test using PepperPy CLI
python -m pepperpy.cli domain run template --task "task_one" --param "test" --pretty

# Run examples from plugin.yaml
python -m pepperpy.cli domain test template
```

## Customizing

To customize this template for your own plugin:

1. Replace `domain` with the appropriate domain (e.g., `llm`, `embedding`, etc.)
2. Replace `template` with your provider name
3. Replace `DomainInterface` with the appropriate domain interface
4. Implement the required methods for your domain
5. Update `plugin.yaml` with your provider's metadata and configuration 