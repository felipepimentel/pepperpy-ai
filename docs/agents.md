# Agent System

The PepperPy AI agent system provides a flexible and extensible way to create and use AI agents. Agents are defined using YAML configuration files and can be easily customized with different capabilities and tools.

## Agent Definition

Agents are defined using YAML files in the `assets/agents` directory. Each agent definition includes:

- Basic information (name, version, description)
- Role configuration
- Required capabilities
- Available tools
- Settings and metadata

Example agent definition:

```yaml
name: code-reviewer
version: "1.0.0"
description: "Expert code reviewer focused on best practices"

capabilities:
  - code_review
  - security_audit
  - performance_analysis

role:
  name: "Code Reviewer"
  description: "Expert code reviewer with deep knowledge"
  instructions: |
    You are an expert code reviewer...

tools:
  - git_diff
  - code_analysis
  - security_scan

settings:
  context_window: 8000
  response_format: "markdown"

metadata:
  author: "PepperPy Team"
  tags: ["code", "review", "quality"]
```

## Using Agents

The agent system provides a simple interface for using pre-defined agents:

```python
from pepperpy.agents import AgentFactory
from pepperpy import Provider

# Create factory
factory = AgentFactory()

# Load agent from YAML
agent = factory.from_yaml("review/code_reviewer.yml")

# Configure provider
agent.use(Provider.anthropic())

# Initialize and use
await agent.initialize()
result = await agent.execute("Review this code for security issues")
```

## Creating Custom Agents

You can create custom agents by:

1. Defining the agent configuration in YAML
2. Implementing the agent class
3. Registering the agent with the factory

Example:

```python
from pepperpy.agents import BaseAgent

class CustomAgent(BaseAgent):
    async def _setup(self) -> None:
        # Initialize capabilities
        for capability in self.config.capabilities:
            if capability == "custom_capability":
                # Initialize custom capability
                pass

    async def _teardown(self) -> None:
        # Cleanup resources
        pass

    async def execute(self, task: str, **kwargs) -> Message:
        # Execute task using provider
        return await self._provider.generate(task)

# Register and use
factory = AgentFactory()
factory.register("custom-agent", CustomAgent)
agent = factory.from_yaml("custom/my_agent.yml")
```

## Capabilities

Agents can have various capabilities that extend their functionality:

- Code analysis
- Security auditing
- Performance optimization
- RAG (Retrieval Augmented Generation)
- And more...

Each capability is loaded dynamically based on the agent's configuration and available dependencies.

## Tools

Tools are specific functionalities that agents can use:

- Git operations
- Code analysis
- Security scanning
- File operations
- And more...

Tools are loaded based on the agent's configuration and can be extended with custom implementations.

## Provider Integration

Agents are provider-agnostic and can work with any supported AI provider:

- OpenAI
- Anthropic
- Cohere
- And more...

The provider is configured at runtime, allowing for easy switching between different providers.

## Best Practices

1. **Agent Design**
   - Keep agents focused on specific tasks
   - Use appropriate capabilities for the task
   - Provide clear instructions in the role configuration

2. **Capability Management**
   - Only include necessary capabilities
   - Handle capability initialization properly
   - Clean up resources when done

3. **Provider Usage**
   - Configure providers appropriately
   - Handle provider-specific settings
   - Consider fallback options

4. **Error Handling**
   - Handle capability initialization errors
   - Manage provider errors gracefully
   - Clean up resources in error cases

## Advanced Usage

### Custom Capabilities

```python
from pepperpy.agents import Capability

class CustomCapability(Capability):
    @property
    def name(self) -> str:
        return "custom_capability"

    async def initialize(self) -> None:
        # Setup capability
        pass

    async def cleanup(self) -> None:
        # Cleanup resources
        pass
```

### Custom Tools

```python
from pepperpy.agents import Tool

class CustomTool(Tool):
    @property
    def name(self) -> str:
        return "custom_tool"

    @property
    def description(self) -> str:
        return "Custom tool for specific tasks"

    async def execute(self, **kwargs) -> Any:
        # Implement tool functionality
        pass
```

## Configuration Reference

### Agent Configuration

| Field | Type | Description |
|-------|------|-------------|
| name | str | Agent name |
| version | str | Agent version |
| description | str | Agent description |
| role | dict | Role configuration |
| capabilities | list | Required capabilities |
| tools | list | Available tools |
| settings | dict | Additional settings |
| metadata | dict | Additional metadata |

### Role Configuration

| Field | Type | Description |
|-------|------|-------------|
| name | str | Role name |
| description | str | Role description |
| instructions | str | Role instructions |

### Settings

| Field | Type | Description |
|-------|------|-------------|
| context_window | int | Context window size |
| response_format | str | Response format |
| custom_settings | any | Additional settings | 