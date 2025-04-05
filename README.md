# PepperPy

A modern Python framework for AI applications with a focus on vertical domain integration.

## Architecture

PepperPy is organized into vertical domains, each with specific responsibilities:

| Domain       | Purpose                              | Status       |
|--------------|--------------------------------------|--------------|
| **LLM**      | Interaction with language models     | Implemented  |
| **RAG**      | Retrieval Augmented Generation       | Planned      |
| **Agent**    | Autonomous agents and assistants     | In Progress  |
| **Tool**     | Tools and external integrations      | Implemented  |
| **Cache**    | Caching strategies and storage       | Implemented  |
| **TTS**      | Text-to-speech operations            | Implemented  |
| **Discovery**| Service and component discovery      | Implemented  |

## Key Design Principles

1. **Vertical Domain Organization**: Each module represents a business domain, not a technical type
2. **Provider-Based Abstraction**: Domain-specific providers for various implementations
3. **Composable Interfaces**: Clean interfaces for building complex systems
4. **Configuration-Driven**: Configuration-first approach with minimal hard-coding

## Example Usage

```python
import asyncio
from pepperpy import PepperPy
from pepperpy.llm import Message

async def main():
    # Initialize with chosen providers
    pepper = PepperPy().with_llm("openai", api_key="your_key_here")
    
    # Initialize providers
    await pepper.initialize()
    
    # Chat with an LLM
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="What is PepperPy?")
    ]
    response = await pepper.llm.chat(messages)
    print(response)
    
    # Generate an embedding
    embedding = await pepper.llm.embed("This is a text to embed")
    
    # Use TTS
    audio_data = await pepper.tts.synthesize("Hello, world!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Project Status

The framework is currently in active development with several domains already implemented.

## Features

- **Provider-Based Architecture**: Easily swap implementations for each domain
- **Async-First Design**: Built for asynchronous operations from the ground up
- **Type-Safe Interfaces**: Strong typing throughout the codebase
- **Configuration Management**: Centralized configuration with provider-specific options
- **Consistent Error Handling**: Domain-specific error hierarchies
- **Extensible**: Create custom providers for any domain

## Installation

```bash
pip install pepperpy
```

## Available Providers

- **LLM**: OpenAI
- **TTS**: Azure TTS
- **Cache**: In-memory, Redis (planned)
- **Tool**: Local, Remote (planned)

## Storage Providers

PepperPy supports various storage backends for persistent data storage:

### SQLite Provider

The SQLite provider offers a lightweight, file-based storage solution that's perfect for development or small-scale applications.

```python
from pepperpy.storage.providers.sqlite import SQLiteProvider, SQLiteConfig

# Configure the SQLite provider
config = SQLiteConfig(
    database_path="./data/my_database.db",
    create_if_missing=True,
)

# Create the provider
provider = SQLiteProvider(config)

# Use the provider to store and retrieve data
async def store_data():
    # Connect to the database
    connection = await provider.get_connection()
    
    # Create a container
    container = StorageContainer(
        name="my_container",
        object_type=MyDataClass,
        description="My data container",
    )
    
    await provider.create_container(container)
    
    # Store an object
    obj = MyDataClass(id="obj1", name="Test Object")
    stored = await provider.put("my_container", obj)
    
    # Retrieve an object
    retrieved = await provider.get("my_container", "obj1")
```

For a complete example, see [examples/sqlite_storage_example.py](examples/sqlite_storage_example.py).

## Documentation

For detailed documentation and examples, see the [examples](./examples) directory.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Discovery and Plugins

PepperPy uses a layered discovery architecture:

1. **Discovery Module** - Provides low-level discovery interfaces
2. **Plugins Module** - Implements high-level plugin management

This separation allows clean architecture with proper separation of concerns. Discovery interfaces define the protocols for finding components, while the plugin system handles the complete lifecycle management.

### 7. Plugin Discovery

PepperPy includes a powerful plugin discovery system that makes it easy to find and use plugins:

```python
from pepperpy.plugin.providers.discovery.plugin_discovery import PluginDiscoveryProvider

discovery = PluginDiscoveryProvider(config={
    "scan_paths": ["path/to/plugins"]
})

await discovery.initialize()
plugins = await discovery.discover_plugins()
```

For more details, see [Discovery and Plugins Relationship](docs/architecture/discovery-plugins-relationship.md) 