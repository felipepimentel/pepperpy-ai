# Creating Plugin Documentation

Every plugin in PepperPy should have its own README.md file that explains how to use it. This guide explains how to create effective documentation for your plugins.

## Documentation Location

Plugin documentation should be placed in the following locations:

1. **Plugin Directory README**: Create a `README.md` file in the plugin directory
   ```
   plugins/
   └── domain/
       └── plugin_name/
           └── README.md  # ← Plugin documentation
   ```

2. **Documentation Directory** (optional but recommended): Create detailed documentation in the docs directory
   ```
   docs/
   └── domain/
       └── plugin_name.md  # ← Detailed documentation
   ```

## Documentation Content

### Plugin README.md

The README.md in the plugin directory should include:

1. **Brief Description**: What the plugin does
2. **CLI Usage Examples**: How to use the plugin via command line
3. **Available Tasks**: List of tasks the plugin supports
4. **Parameters**: Description of parameters for each task
5. **Configuration Options**: Available configuration settings
6. **Troubleshooting**: Common issues and solutions
7. **Direct Usage**: How to use the plugin directly in Python code

### Template

Use the [Plugin README Template](plugin_readme_template.md) as a starting point for your documentation.

## CLI Documentation Examples

Every plugin should document how to use it via the CLI. Here's the format to follow:

```bash
# Basic command with explanations
python -m pepperpy.cli domain run domain/plugin_name --input '{"task": "task_name", "param1": "value1"}'
```

Include examples for:

1. **Basic Usage**: The simplest way to use the plugin
2. **Advanced Usage**: More complex usage scenarios
3. **Parameter Variations**: Different parameter combinations
4. **Configuration Options**: How to configure the plugin

## Parameters Documentation

Document each parameter using this format:

```
**Parameters:**
- `param_name` (type, required/optional): Description of the parameter
  - `nested_param` (type, required/optional): Description of nested parameter
- `another_param` (type, required/optional): Description of another parameter
```

## Input/Output Format Documentation

Document the input and output formats:

```json
// Input format example:
{
  "task": "task_name",
  "param1": "value1",
  "param2": {
    "nested_param": "value"
  }
}

// Output format example:
{
  "result": "success",
  "data": {
    "field1": "value1",
    "field2": "value2"
  }
}
```

## Troubleshooting Section

Include common errors and their solutions:

```
## Troubleshooting

### Error: "Provider not found"

If you encounter this error:

1. Check that the plugin is properly registered:
   ```bash
   python -m pepperpy.cli domain list
   ```

2. Ensure the plugin directory structure is correct:
   ```
   plugins/
   └── domain/
       └── plugin_name/
           ├── plugin.yaml
           └── provider.py
   ```
```

## Python Usage Examples

Include examples of how to use the plugin directly in Python code:

```python
import asyncio
from plugins.domain.plugin_name.provider import PluginClass

async def use_plugin():
    plugin = PluginClass()
    await plugin.initialize()
    
    try:
        result = await plugin.execute({
            "task": "task_name",
            "param1": "value1"
        })
        print(result)
    finally:
        await plugin.cleanup()

if __name__ == "__main__":
    asyncio.run(use_plugin())
```

## Documentation Review Checklist

Before submitting plugin documentation, ensure it:

- [ ] Includes a clear description of the plugin's purpose
- [ ] Documents all available tasks
- [ ] Lists all parameters for each task
- [ ] Provides working CLI examples
- [ ] Includes troubleshooting information
- [ ] Shows how to use the plugin directly in Python
- [ ] Links to more detailed documentation if available
- [ ] Has been tested for accuracy (commands work as documented)

## Sample Documentation

For examples of well-documented plugins, see:

- [Repository Analyzer Plugin](../../plugins/workflow/repository_analyzer/README.md)
- [LLM Completion Plugin](../../plugins/workflow/llm_completion/README.md)
- [Content Generator Plugin](../../plugins/workflow/content_generator/README.md)

## Automating Documentation Generation

You can use the documentation generation script to create a basic README template:

```bash
python -m pepperpy.tools.generate_docs --plugin domain/plugin_name --output plugins/domain/plugin_name/README.md
```

This will create a basic template that you can then customize with your plugin's specific details. 