# PepperPy AI

A flexible AI library with modular provider support and dynamic agent capabilities.

## Features

- Dynamic agent system with YAML-based configuration
- Pluggable provider support (OpenAI, Anthropic, Cohere)
- Extensible capabilities and tools
- Modular architecture with clear separation of concerns
- Strong typing and async support

## Installation

```bash
# Basic installation
pip install pepperpy-ai

# With specific provider support
pip install pepperpy-ai[openai]      # OpenAI support
pip install pepperpy-ai[anthropic]   # Anthropic support
pip install pepperpy-ai[cohere]      # Cohere support

# With capability support
pip install pepperpy-ai[embeddings]  # Embedding support
pip install pepperpy-ai[code]        # Code analysis support
pip install pepperpy-ai[rag]         # RAG support
pip install pepperpy-ai[text]        # Text processing
pip install pepperpy-ai[pdf]         # PDF processing

# Complete installation
pip install pepperpy-ai[complete]    # All features
```

## Quick Start

```python
from pepperpy.agents import AgentFactory
from pepperpy_core import Provider

# Create factory
factory = AgentFactory()

# Load agent from YAML definition
agent = factory.from_yaml("review/code_reviewer.yml")

# Configure provider
agent.use(Provider.anthropic())

# Initialize and use
await agent.initialize()
result = await agent.execute("Review this code for security issues")
print(result)
```

## Creating Custom Agents

1. Define agent in YAML:

```yaml
# assets/agents/custom/my_agent.yml
name: my-custom-agent
version: "1.0.0"
description: "Custom agent for specific tasks"

capabilities:
  - code_review
  - security_audit

role:
  name: "Custom Agent"
  description: "Specialized agent for custom tasks"
  instructions: |
    You are a specialized agent...

tools:
  - custom_tool
  - another_tool

settings:
  context_window: 8000
```

2. Implement agent class:

```python
from pepperpy.agents import BaseAgent

class CustomAgent(BaseAgent):
    async def _setup(self) -> None:
        # Initialize capabilities
        pass

    async def _teardown(self) -> None:
        # Cleanup resources
        pass

    async def execute(self, task: str, **kwargs) -> Message:
        # Execute task
        return await self._provider.generate(task)

# Register and use
factory = AgentFactory()
factory.register("my-custom-agent", CustomAgent)
agent = factory.from_yaml("custom/my_agent.yml")
```

## Documentation

For detailed documentation, visit [docs.pepperpy.ai](https://docs.pepperpy.ai).

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
