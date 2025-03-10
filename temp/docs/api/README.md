# PepperPy API Reference

This section provides detailed reference documentation for the PepperPy framework's API.

## Modules

- [Types](./types.md): Type definitions.
- [Errors](./errors.md): Error handling.
- [Utils](./utils.md): Utility functions.
- [Config](./config.md): Configuration management.
- [CLI](./cli.md): Command-line interface.
- [Registry](./registry.md): Component registry.
- [Interfaces](./interfaces.md): Interface definitions.
- [Memory](./memory.md): Memory management.
- [Cache](./cache.md): Caching system.
- [Storage](./storage.md): Storage system.
- [Workflows](./workflows.md): Workflow management.
- [Events](./events.md): Event-driven architecture.
- [Plugins](./plugins.md): Plugin system.
- [Streaming](./streaming.md): Streaming functionality.
- [LLM](./llm.md): Integration with large language models.
- [RAG](./rag.md): Retrieval-augmented generation.
- [HTTP](./http.md): HTTP client and server.
- [Data](./data.md): Data processing and persistence.

## API Conventions

### Naming Conventions

- Module names are in lowercase.
- Class names are in PascalCase.
- Function and method names are in snake_case.
- Constants are in UPPERCASE.
- Private attributes and methods are prefixed with an underscore.

### Type Hints

All public APIs include type hints to provide better IDE support and enable static type checking.

### Error Handling

All errors raised by the framework are subclasses of `PepperPyError`. Each module has its own error classes that inherit from `PepperPyError`.

### Async/Await

Most of the framework's APIs are designed to be used with async/await. Synchronous versions of some APIs are provided for convenience.

### Documentation

All public APIs include docstrings that describe their purpose, parameters, return values, and exceptions.

## Example Usage

```python
import asyncio
from pepperpy.llm import get_provider, generate_text

async def main():
    # Initialize a provider
    provider = get_provider("openai")
    
    # Generate text
    response = await generate_text(provider, "Hello, world!")
    print(response)

asyncio.run(main())
``` 