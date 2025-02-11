# Pepperpy

A powerful AI agent framework with zero-config capabilities.

## Features

- 🚀 **Zero-Config Setup**: Get started quickly with sensible defaults
- 🤖 **Flexible Agent System**: Create and manage AI agents with ease
- 🔄 **Built-in Workflows**: Pre-defined workflows for common tasks
- 💾 **Automatic Caching**: Reduce costs and improve performance
- 🔌 **Plugin Architecture**: Extend functionality through hooks
- 📊 **Integrated Monitoring**: Built-in logging and metrics
- 🛠️ **CLI Tools**: Command-line interface for quick testing

## Installation

```bash
# Install using Poetry (recommended)
poetry add pepperpy

# Or using pip
pip install pepperpy
```

## Quick Start

```python
from pepperpy import PepperpyClient

async def main():
    # Auto-configured client
    async with PepperpyClient.auto() as client:
        # Simple research example
        results = await client.run(
            "research_assistant",
            "analyze",
            topic="AI in Healthcare",
            max_sources=5
        )
        print(results.summary)

        # Advanced workflow example
        results = await client.run_workflow(
            "research/comprehensive",
            topic="AI in Healthcare",
            requirements={
                "depth": "expert",
                "focus": ["academic", "industry"]
            }
        )
        print(results.key_findings)

# Run the example
import asyncio
asyncio.run(main())
```

## Configuration

Pepperpy can be configured through:

1. Environment variables (`.env` file)
2. Configuration file (`.pepperpy/config.yml`)
3. Programmatic configuration

Example `.env` file:
```bash
PEPPERPY_API_KEY=your-api-key
PEPPERPY_PROVIDER=openai
PEPPERPY_MODEL=gpt-4-turbo-preview
```

Example `config.yml`:
```yaml
provider:
  type: openai
  model: gpt-4-turbo-preview
  temperature: 0.7

memory:
  type: redis
  url: redis://localhost:6379

cache:
  enabled: true
  store: memory
```

## CLI Usage

```bash
# Run a research task
pepperpy run agent research_assistant --topic "AI in Healthcare"

# Execute a workflow
pepperpy run workflow research/comprehensive --topic "AI in Healthcare"

# List available agents
pepperpy list agents

# Show configuration
pepperpy config show
```

## Advanced Usage

### Custom Hooks

```python
def my_logger_hook(context):
    print(f"Processing: {context.current_step}")

client.register_hook("after_agent_call", my_logger_hook)
```

### Cache Configuration

```python
# Enable caching with Redis
client = PepperpyClient(
    cache_enabled=True,
    cache_store="redis",
    cache_config={
        "url": "redis://localhost:6379"
    }
)
```

### Custom Workflows

```python
# Define a workflow in .pepper_hub/workflows/custom.yml
name: my_workflow
steps:
  - agent: research_assistant
    action: analyze
    params:
      depth: comprehensive
  - agent: summarizer
    action: summarize
    params:
      style: concise

# Run the workflow
results = await client.run_workflow("my_workflow", topic="...")
```

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/pepperpy.git
cd pepperpy

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linters
poetry run black .
poetry run ruff check .
poetry run mypy .
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
