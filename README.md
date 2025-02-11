# Pepper Hub

A centralized hub for managing and loading AI artifacts like agents, prompts, and workflows. Pepper Hub provides a robust and extensible framework for building AI-powered applications with a focus on modularity, type safety, and maintainability.

## Core Concepts

### The Hub Architecture

Pepper Hub is built around the concept of a centralized repository of AI artifacts that can be easily shared, versioned, and reused across projects. The hub consists of three main components:

1. **Artifacts**: Pre-built, tested, and documented AI components that can be easily integrated into your applications
2. **Registry**: A central system for managing and loading artifacts
3. **Provider System**: A pluggable system for integrating with different AI providers (OpenAI, Anthropic, etc.)

### Types of Artifacts

- **Agents**: Intelligent components that can perform specific tasks (e.g., Research Assistant, Code Reviewer)
- **Prompts**: Carefully crafted templates for interacting with AI models
- **Workflows**: Reusable sequences of operations combining multiple agents and prompts

## Features

### Core Features

- **Artifact Management**
  - Centralized registry for agents, prompts, and workflows
  - Version control and dependency management
  - Hot-reloading of artifacts during development

- **Type Safety & Validation**
  - Full type hints and runtime validation
  - Automatic validation of configurations
  - Type-safe prompt templates

- **Provider System**
  - Unified interface for multiple AI providers
  - Easy provider switching and fallback
  - Automatic rate limiting and retries

### Advanced Features

- **Memory Management**
  - Built-in support for different memory types
  - Configurable memory scopes
  - Memory persistence and serialization

- **Event System**
  - Rich event system for monitoring and logging
  - Custom event handlers and middleware
  - Telemetry and analytics support

- **Workflow Engine**
  - Complex workflow orchestration
  - Parallel and sequential execution
  - Error handling and recovery

## Installation

```bash
pip install pepper-hub
```

Or with Poetry:

```bash
poetry add pepper-hub
```

## Quick Start

### Using Pre-built Artifacts

```python
from pepper_hub import Hub

# Initialize the hub
hub = Hub()

# Load a pre-built research assistant
agent = hub.load_agent(
    "research_assistant",
    config={
        "provider": {
            "api_key": "your-api-key"
        }
    }
)

# Use the agent
result = await agent.analyze_paper(paper)
```

### Creating Custom Artifacts

```python
from pepper_hub.agents import BaseAgent
from pepper_hub.decorators import register_agent

@register_agent("custom_assistant")
class CustomAssistant(BaseAgent):
    async def analyze(self, data):
        prompt = self.prompt_registry.get_prompt("custom.analyze")
        return await self.provider.generate(prompt.render(data=data))
```

## Project Structure

```
pepper_hub/
├── artifacts/                # Pre-built artifacts
│   ├── research_assistant/
│   │   ├── agent.py         # Agent implementation
│   │   ├── config.yml       # Agent configuration
│   │   └── prompts/         # Agent-specific prompts
│   └── code_reviewer/
│       └── ...
├── agents/
│   ├── base.py              # Base agent classes
│   ├── registry.py          # Agent registry
│   └── providers/           # Provider implementations
├── prompts/
│   ├── base.py              # Base prompt classes
│   ├── registry.py          # Prompt registry
│   └── templates/           # Shared prompt templates
└── workflows/
    ├── base.py              # Base workflow classes
    ├── registry.py          # Workflow registry
    └── engine.py            # Workflow execution engine
```

## Configuration

### Agent Configuration

```yaml
name: Research Assistant
description: An intelligent research assistant

provider:
  type: openai
  model: gpt-4
  temperature: 0.7
  max_tokens: 2000

memory:
  type: in_memory
  scope: session

prompts:
  - name: research.analyze
    template: |
      Analyze the following paper:
      {{ paper }}
```

### Provider Configuration

```yaml
providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    default_model: gpt-4
    timeout: 30
    retries: 3
```

## Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pepper-hub.git
   cd pepper-hub
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Run tests:
   ```bash
   poetry run pytest
   ```

4. Start development server:
   ```bash
   poetry run pepper-hub dev
   ```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Process

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Implement your changes
5. Run tests and linting (`poetry run pytest && poetry run ruff check .`)
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
