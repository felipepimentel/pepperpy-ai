# Pepperpy: A Modern AI Agent Framework

Pepperpy is a powerful and flexible framework for building AI-powered applications using large language models. It provides a high-level, declarative API for creating and managing AI agents and workflows.

## Key Features

- **Unified Configuration**: Simple initialization and configuration management
- **Declarative Workflows**: Define complex AI workflows using YAML
- **High-Level API**: Work with agents and workflows without dealing with low-level details
- **Type Safety**: Full type hints and validation throughout the codebase
- **Extensible**: Plugin system for custom providers, capabilities, and integrations

## Quick Start

1. Install the package:
```bash
pip install pepperpy
```

2. Set up your environment:
```bash
export PEPPERPY_API_KEY="your-api-key"
export PEPPERPY_PROVIDER="openrouter"  # or other supported provider
```

3. Create a simple research workflow:

```python
from pepperpy import Pepperpy

# Initialize the framework
pepper = Pepperpy.init(storage_dir=".pepper_hub")

# Run a research workflow
async def research_topic():
    results = await pepper.hub.workflow_engine.run(
        workflow_name="research",
        input_data={
            "topic": "AI Safety",
            "max_sources": 5
        }
    )
    return results

# Run synchronously if preferred
results = pepper.hub.workflow_engine.run_sync(
    workflow_name="research",
    input_data={"topic": "AI Safety"}
)
```

## Workflow Definitions

Pepperpy uses YAML files to define workflows. Here's an example research workflow:

```yaml
name: research_workflow
version: "0.1.0"
description: "Research assistant workflow for analyzing topics"

agent:
  name: research_assistant
  version: "0.1.0"

steps:
  - name: analyze_topic
    method: analyze_topic
    inputs:
      - name: topic
        type: str
        description: "Research topic to analyze"
    outputs:
      - name: summary
        type: str
        description: "Initial topic analysis"

flow:
  - step: analyze_topic
    inputs:
      topic: "${workflow.input.topic}"
    outputs:
      summary: "${workflow.output.summary}"

validation:
  input_schema:
    type: object
    required: ["topic"]
    properties:
      topic:
        type: string
        description: "Research topic to analyze"
```

## Project Structure

```
pepperpy/
├── __init__.py           # Main package initialization
├── core/                 # Core framework components
├── hub/                  # Asset and workflow management
├── providers/            # AI provider implementations
├── agents/              # Built-in agent implementations
└── monitoring/          # Logging and observability
```

## Configuration

Pepperpy can be configured through environment variables, YAML files, or programmatically:

```python
# Environment variables
PEPPERPY_STORAGE_DIR=".pepper_hub"
PEPPERPY_PROVIDER="openrouter"
PEPPERPY_MODEL="openai/gpt-4-turbo"
PEPPERPY_API_KEY="your-api-key"

# Or programmatically
pepper = Pepperpy.init(
    storage_dir=".pepper_hub",
    provider_type="openrouter",
    model="openai/gpt-4-turbo",
    api_key="your-api-key"
)
```

## Creating Custom Agents

1. Define the agent class:

```python
from pepperpy.hub.agents import Agent
from typing import Any

class CustomAgent(Agent[str]):
    """Custom agent implementation."""

    async def run(self, input_data: str) -> Any:
        """Implement the agent's main functionality."""
        # Your implementation here
        result = await self.execute(f"Process: {input_data}")
        return result
```

2. Register the agent:

```python
from pepperpy.hub.agents import AgentRegistry

# Register the agent
agent = CustomAgent(config)
AgentRegistry.register("custom_agent", agent)

# Use the agent
agent = pepper.get_agent("custom_agent")
result = await agent.run("some input")
```

## Examples

Check out the `examples/` directory for more detailed examples:

- `research_workflow_example.py`: Demonstrates the workflow system
- `simple_chat.py`: Basic chat agent implementation
- `custom_agent.py`: Creating custom agents

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
