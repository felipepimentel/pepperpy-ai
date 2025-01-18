# PepperPy

A Python library for building flexible and powerful AI agents.

## Features

- **Modular Agent Architecture**: Build agents using composable components and frameworks
- **Multiple LLM Providers**: Support for OpenAI, Anthropic, OpenRouter and more
- **Flexible Frameworks**: ReAct, Chain-of-Thought, and Tree-of-Thoughts implementations
- **Rich Tools**: Web search, file operations, calculations and more
- **State Management**: Built-in state tracking and memory management
- **Extensible**: Easy integration with external frameworks like AutoGen, LangChain and more

## Installation

```bash
# Basic installation
pip install pepperpy

# With all dependencies
pip install pepperpy[all]

# With specific features
pip install pepperpy[llms]  # Additional LLM providers
pip install pepperpy[tools]  # Additional tools
pip install pepperpy[data-stores]  # Vector stores and embeddings
pip install pepperpy[integrations]  # External framework integrations
```

## Quick Start

```python
from pepperpy.agents import ReActAgent
from pepperpy.agents.base.interfaces import AgentConfig

# Configure the agent
config = AgentConfig(
    agent_id="my_agent",
    model={
        "provider": "openai",
        "model_name": "gpt-4-turbo-preview"
    }
)

# Create and use the agent
async with ReActAgent(config) as agent:
    response = await agent.process({
        "request": "What is the weather in Paris?"
    })
    print(response.response)
```

## Project Structure

```
pepperpy/
├── agents/                     # Agent architecture and logic
│   ├── base/                  # Base interfaces and abstractions
│   ├── frameworks/            # Reasoning framework implementations
│   ├── integrations/          # External framework adapters
│   ├── configurations/        # Agent configuration templates
│   ├── templates/             # Agent templates and prompts
│   └── utils/                 # Agent utilities
│
├── llms/                      # LLM provider integrations
├── data_stores/               # Vector stores and embeddings
├── tools/                     # Tool implementations
├── pipelines/                 # Execution pipelines
├── memory/                    # Memory management
├── evaluation/                # Monitoring and evaluation
└── config/                    # Global configuration
```

## Documentation

For detailed documentation, visit [docs/](docs/).

## Examples

Check out the [examples/](examples/) directory for more usage examples.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the terms of the MIT license. See [LICENSE](LICENSE) for more details.
