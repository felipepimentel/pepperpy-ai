# API Reference

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