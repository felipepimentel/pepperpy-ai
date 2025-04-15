# Plugin Testing in PepperPy

This document explains PepperPy's approach to plugin testing without including test/mock files inside plugin directories.

## Core Concept

PepperPy's plugin testing system follows these key principles:

1. **Configuration as Documentation**: Examples are defined in plugin.yaml files, not separate test files
2. **CLI-Based Testing**: Plugins are tested via a dedicated CLI tool 
3. **Centralized Testing**: Actual test implementation exists outside plugin directories
4. **No Test Files in Plugins**: Keeps plugin directories clean and focused

## Implementation Details

### Plugin Configuration

Each plugin includes examples directly in its `plugin.yaml` file:

```yaml
# Regular plugin configuration
name: domain/provider_name
# ... other configuration ...

# Examples section
examples:
  - name: "basic_example"
    description: "Basic usage example"
    input:
      parameter1: "value1"
      parameter2: "value2"
    expected_output:
      status: "success"
      result: "expected result pattern"
```

### CLI Testing Tool

A dedicated CLI tool is provided for testing plugins:

```bash
# Test plugin with examples from plugin.yaml
bin/pepperpy-plugin test plugins/domain/provider

# Run plugin with custom input
bin/pepperpy-plugin run plugins/domain/provider --input '{"param": "value"}'

# Run plugin with input from file
bin/pepperpy-plugin run plugins/domain/provider --input input.json
```

### Testing Framework

The testing framework includes:

1. **Plugin Runner**: A utility for executing plugins programmatically
2. **Plugin Tester**: A utility for testing plugins using examples from plugin.yaml
3. **CLI Interface**: A command-line interface for testing and running plugins

### Centralized Test Implementation

Instead of placing tests within plugin directories, tests are organized in a centralized location:

```
tests/
├── plugins/                # Plugin tests
│   ├── conftest.py         # Common test fixtures
│   └── domain/             # Tests for domain plugins
│       └── provider/       # Tests for specific provider
│           └── test_provider.py  # Test implementation
```

## How to Use

### For Plugin Authors

1. **Define Examples in plugin.yaml**:

```yaml
examples:
  - name: "example_name"
    description: "Example description"
    input:
      parameter: "value"
    expected_output:
      status: "success"
```

2. **Test Plugin via CLI**:

```bash
bin/pepperpy-plugin test plugins/your/plugin
```

3. **Run Custom Examples**:

```bash
bin/pepperpy-plugin run plugins/your/plugin --input '{"param": "custom_value"}'
```

### For Test Developers

1. **Write Tests Using Centralized Framework**:

```python
"""Tests for domain/provider plugin."""

import pytest
from pepperpy.domain import create_provider

@pytest.mark.asyncio
async def test_provider_examples():
    """Test provider using examples from plugin.yaml."""
    # Load plugin.yaml examples
    from pepperpy.plugin import get_plugin_config
    config = get_plugin_config("domain", "provider")
    
    examples = config.get("examples", [])
    if not examples:
        pytest.skip("No examples defined in plugin.yaml")
    
    # Create provider
    provider = create_provider("domain", "provider")
    
    # Run tests for each example
    for example in examples:
        input_data = example.get("input", {})
        expected = example.get("expected_output", {})
        
        async with provider:
            result = await provider.execute(input_data)
            
            # Validate result
            for key, value in expected.items():
                assert key in result
                assert result[key] == value
```

## Benefits

1. **Clean Plugin Structure**: Plugins contain only essential implementation files
2. **Self-Documenting**: Examples serve as both tests and documentation
3. **Easy Testing**: Simple CLI commands for testing plugins
4. **Consistent Approach**: Standardized testing methodology
5. **Separation of Concerns**: Implementation and testing are separate

## Future Improvements

1. **Enhanced Validation**: More sophisticated result validation
2. **Test Report Generation**: Detailed test reports
3. **CI Integration**: Automatic testing of all plugins
4. **Example Templates**: Standard templates for common examples 