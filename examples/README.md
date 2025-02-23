# Pepperpy Examples

This directory contains examples demonstrating how to use the Pepperpy framework.
The examples are organized by complexity level to help you get started and
gradually explore more advanced features.

## Structure

- `basic/`: Basic examples showing core functionality
  - `hello_world.py`: Simple example showing basic setup
  - `simple_agent.py`: Example of creating and using a basic agent

- `intermediate/`: Intermediate examples showing more complex features
  - `custom_provider.py`: Example of creating a custom provider
  - `workflow_example.py`: Example of creating and running workflows

- `advanced/`: Advanced examples showing complex scenarios
  - `distributed_system.py`: Example of distributed system setup
  - `complex_workflow.py`: Example of complex workflow with multiple agents

## Getting Started

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Run an example:
   ```bash
   poetry run python examples/basic/hello_world.py
   ```

## Example Categories

### Basic Examples
Basic examples demonstrate core functionality and are a good starting point
for new users. These examples focus on:
- Framework initialization
- Basic configuration
- Simple agent creation and usage
- Resource management basics

### Intermediate Examples
Intermediate examples show more complex features and are suitable for users
who are familiar with the basics. These examples cover:
- Custom provider implementation
- Workflow creation and management
- Event handling
- Resource lifecycle management

### Advanced Examples
Advanced examples demonstrate complex scenarios and are intended for users
who want to leverage the full power of the framework. These examples show:
- Distributed system setup
- Complex workflows with multiple agents
- Custom protocol implementation
- Advanced monitoring and metrics

## Example Template
Each example follows this template:
```python
"""Example Name: [Name]
Description: [Brief description]
Category: [basic|intermediate|advanced]
Dependencies: [List of dependencies]
"""

import pepperpy as pp

def main():
    # Setup
    config = pp.Config()
    
    # Example implementation
    result = pp.run_example(config)
    
    # Cleanup
    pp.cleanup()

if __name__ == "__main__":
    main()
```

## Contributing
When adding new examples:
1. Follow the example template
2. Add appropriate documentation
3. Include validation tests
4. Update this README
5. Ensure all examples run without errors 