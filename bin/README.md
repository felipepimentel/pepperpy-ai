# PepperPy CLI Tools

This directory contains command-line tools for working with PepperPy.

## pepperpy-plugin

A CLI tool for testing and running PepperPy plugins without requiring test files in plugin directories.

### Usage

```bash
# Test a plugin with examples from plugin.yaml
./pepperpy-plugin test plugins/domain/provider

# Run a plugin with custom input
./pepperpy-plugin run plugins/domain/provider --input '{"param": "value"}'

# Run a plugin with input from file
./pepperpy-plugin run plugins/domain/provider --input input.json --pretty
```

### How It Works

This tool uses the plugin testing framework in `pepperpy/plugin/testing.py` to:

1. Load plugin configurations from `plugin.yaml`
2. Import plugin providers dynamically
3. Execute plugin examples or custom inputs
4. Validate results against expected outputs

### Benefits

- Test plugins without creating test files in plugin directories
- Run plugins directly from the command line for quick testing
- Define examples in `plugin.yaml` as both documentation and tests
- Centralized testing with consistent approach

## More Tools

Additional CLI tools will be added here in the future. 