# API Reference

This section provides detailed documentation for the Pepperpy API.

## Core API

### Pepperpy Class

The main entry point for the library.

```python
from pepperpy import Pepperpy

# Create instance
pepper = await Pepperpy.create(
    api_key="your-api-key",      # Optional: Use environment variable
    model="openai/gpt-4",        # Optional: Default model
    temperature=0.7,             # Optional: Response creativity
    max_tokens=2048,             # Optional: Maximum response length
    style="detailed",            # Optional: Response style
    format="text"                # Optional: Output format
)

# Or use interactive setup
pepper = await Pepperpy.quick_start()
```

### Basic Methods

#### ask()
Ask a simple question and get a direct response.

```python
result = await pepper.ask(
    "What is artificial intelligence?",
    style="concise",              # Optional: concise, detailed, technical
    format="text",                # Optional: text, markdown, json
    temperature=0.7,              # Optional: Response creativity
    max_tokens=2048               # Optional: Maximum response length
)
print(result)
```

#### chat()
Start an interactive chat session.

```python
# Start with initial message
await pepper.chat("Tell me about Python")

# Or start blank chat
await pepper.chat()

# Available commands during chat:
# - /help: Show available commands
# - /clear: Clear chat history
# - /save: Save conversation
# - /style: Change response style
# - /format: Change output format
```

#### research()
Conduct in-depth research on a topic.

```python
result = await pepper.research(
    topic="Impact of AI in Healthcare",
    depth="detailed",            # Optional: basic, detailed, comprehensive
    style="business",            # Optional: casual, business, academic
    format="report",             # Optional: summary, bullets, report
    max_sources=10               # Optional: Maximum sources to use
)

print(result.tldr)       # Quick summary
print(result.full)       # Full report
print(result.bullets)    # Key points
print(result.references) # Sources
```

### Hub API

#### Teams
Create and manage teams for complex tasks.

```python
# Use pre-configured team
team = await pepper.hub.team("research-team")

# Run team task
async with team.run("Analyze AI trends") as session:
    print(f"Step: {session.current_step}")
    print(f"Progress: {session.progress}")
    print(f"Thoughts: {session.thoughts}")
    
    if session.needs_input:
        session.provide_input("More details")
```

#### Custom Agents
Create and share custom agents.

```python
# Create custom agent
agent = await pepper.hub.create_agent(
    name="technical-researcher",
    base="researcher",           # Inherit from base agent
    config={
        "style": "technical",
        "depth": "deep"
    }
)

# Use agent
result = await agent.research("Topic")

# Share agent
await pepper.hub.publish("technical-researcher")
```

#### Workflows
Create custom workflows for complex tasks.

```python
# Create workflow
workflow = await pepper.hub.create_workflow(
    name="research-write-review",
    steps=[
        {
            "agent": "researcher",
            "action": "research",
            "output": "research_results"
        },
        {
            "agent": "writer",
            "action": "write",
            "input": "research_results",
            "output": "article"
        }
    ]
)

# Run workflow
result = await workflow.run("Topic")
```

## Configuration

### Environment Variables

```bash
# Required
PEPPERPY_API_KEY=your-api-key

# Optional
PEPPERPY_MODEL=openai/gpt-4
PEPPERPY_TEMPERATURE=0.7
PEPPERPY_MAX_TOKENS=2048
PEPPERPY_STYLE=detailed
PEPPERPY_FORMAT=text
```

### Advanced Configuration

```python
pepper = await Pepperpy.create(
    # Model settings
    model="openai/gpt-4",
    temperature=0.7,
    max_tokens=2048,
    
    # Response settings
    style="technical",
    format="markdown",
    
    # Performance settings
    cache_enabled=True,
    cache_ttl=3600,
    request_timeout=30.0,
    max_retries=3,
    
    # Monitoring settings
    metrics_enabled=True,
    log_level="DEBUG",
    
    # Hub settings
    hub_sync_interval=300,
    hub_auto_update=True
)
```

## Error Handling

```python
from pepperpy.core.errors import PepperpyError

try:
    result = await pepper.ask("Question")
except PepperpyError as e:
    print(f"Error: {e}")
```

## Additional Resources

- [Getting Started Guide](../getting_started.md)
- [Examples](../../examples/)
- [Jupyter Notebooks](../../examples/notebooks/)

## Core Modules

### `pepperpy.core`
- `pepperpy.core.utils`: Core utilities and helpers
- `pepperpy.core.config`: Configuration management
- `pepperpy.core.context`: Context management
- `pepperpy.core.lifecycle`: Lifecycle management

## Providers

### `pepperpy.providers`
- `pepperpy.providers.llm`: LLM providers
- `pepperpy.providers.embedding`: Embedding providers
- `pepperpy.providers.vector_store`: Vector store providers
- `pepperpy.providers.memory`: Memory providers

## Capabilities

### `pepperpy.capabilities`
- `pepperpy.capabilities.base`: Base capability interface
- `pepperpy.capabilities.tools`: Tool implementations
  - `pepperpy.capabilities.tools.functions.core`: Core tool functions
  - `pepperpy.capabilities.tools.functions.io`: IO tool functions
  - `pepperpy.capabilities.tools.functions.ai`: AI tool functions
  - `pepperpy.capabilities.tools.functions.media`: Media tool functions
  - `pepperpy.capabilities.tools.functions.system`: System tool functions

## Middleware

### `pepperpy.middleware`
- `pepperpy.middleware.base`: Base middleware interface
- `pepperpy.middleware.handlers`: Middleware handlers

## Validation

### `pepperpy.validation`
- `pepperpy.validation.rules`: Validation rules
- `pepperpy.validation.validators`: Validator implementations

## Persistence

### `pepperpy.persistence`
- `pepperpy.persistence.base`: Base persistence interface
- `pepperpy.persistence.storage`: Storage implementations
- `pepperpy.persistence.cache`: Cache implementations
- `pepperpy.persistence.serializer`: Serializer implementations

## Extensions

### `pepperpy.extensions`
- `pepperpy.extensions.base`: Base extension interface
- `pepperpy.extensions.plugins`: Plugin implementations

## Type Definitions

### `pepperpy.types`
- Common type definitions and interfaces used across the framework

## Core APIs

### Client API
- [PepperPyAI](./client.md) - Main client class for interacting with AI services
- [Config](./config.md) - Configuration management

### Agents
- [BaseAgent](./agents/base_agent.md) - Base class for all agents
- [ChatAgent](./agents/chat_agent.md) - Agent for chat interactions
- [CompletionAgent](./agents/completion_agent.md) - Agent for text completion

### Providers
- [OpenAIProvider](./providers/openai.md) - OpenAI integration
- [AnthropicProvider](./providers/anthropic.md) - Anthropic integration
- [BaseProvider](./providers/base.md) - Base provider interface

### Types and Utilities
- [Types](./types.md) - Common type definitions
- [Exceptions](./exceptions.md) - Custom exceptions
- [Cache](./cache.md) - Caching utilities

## Module Reference

### Core Modules
- [pepperpy.client](./modules/client.md)
- [pepperpy.config](./modules/config.md)
- [pepperpy.cache](./modules/cache.md)

### Agent Modules
- [pepperpy.agents](./modules/agents.md)
- [pepperpy.base](./modules/base.md)

### Provider Modules
- [pepperpy.providers](./modules/providers.md)
- [pepperpy.llm](./modules/llm.md)

### Utility Modules
- [pepperpy.types](./modules/types.md)
- [pepperpy.exceptions](./modules/exceptions.md)

## Examples

For code examples and usage patterns, see the [Examples](../examples/index.md) section. 