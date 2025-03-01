# Agent Providers

This directory contains provider implementations for agent capabilities in the PepperPy framework.

## Available Components

- **Base Provider**: Base classes and interfaces for agent providers
- **Client**: Client implementation for interacting with agents
- **Domain**: Domain models for agent providers
- **Engine**: Engine implementation for agent execution
- **Factory**: Factory for creating agent instances
- **Manager**: Manager for handling multiple agents
- **Types**: Type definitions for agent providers

## Usage

```python
from pepperpy.agents.providers import BaseProvider, AgentFactory, AgentManager

# Create an agent factory
factory = AgentFactory()

# Create an agent manager
manager = AgentManager()

# Create a custom agent provider
class MyAgentProvider(BaseProvider):
    # Implementation details
    pass
```

## Adding New Providers

To add a new provider:

1. Create a new file in this directory
2. Implement the appropriate base classes
3. Register your provider in the `__init__.py` file

## Migration Note

These providers were previously located in `pepperpy/providers/agent/`. The move to this domain-specific location improves modularity and maintainability. 