# PepperPy Plugin System

## Architecture Overview

The PepperPy Plugin System provides a modular, extensible architecture for plugin management. The system is designed around the following core components:

1. **Plugin Registry** - Manages plugin registration, discovery, and lookup
2. **Plugin Manager** - Handles plugin instances, dependencies, and lifecycle
3. **Resources** - Provides shared resource management
4. **Extensions** - Offers additional plugin features like state persistence and hot reloading

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Plugin System                           │
├─────────────┬─────────────┬─────────────┬─────────────┬─────┘
│             │             │             │             │
▼             ▼             ▼             ▼             ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   registry  │  │   manager   │  │  resources  │  │ extensions  │
└─────┬───────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
      │                 │                │                │
      ▼                 ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Registration│  │  Instance   │  │  Resource   │  │    State    │
│  Discovery  │  │ Management  │  │ Management  │  │ Persistence │
│   Aliases   │  │Dependency   │  │   Pooling   │  │ Hot Reload  │
│  Fallbacks  │  │ Resolution  │  │   Cleanup   │  │             │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

## Core Files

The plugin system is organized into the following core files:

1. **registry.py** - Plugin registration and discovery
2. **manager.py** - Plugin instance and dependency management
3. **resources.py** - Resource pooling and lifecycle management
4. **extensions.py** - Additional plugin features
5. **plugin.py** - Base plugin class and lifecycle methods

## Key Concepts

### Plugin Types and Providers

Plugins in PepperPy are identified by a combination of "type" and "provider":

- **Type**: The category or functionality (e.g., "llm", "embeddings", "rag")
- **Provider**: The specific implementation (e.g., "openai", "anthropic", "local")

For example, a plugin might be identified as `"llm/openai"` where "llm" is the type and "openai" is the provider.

### Plugin Lifecycle

Plugins follow a standard lifecycle:

1. **Registration** - Plugin classes are registered with the system
2. **Discovery** - Plugin providers are discovered from the filesystem or other sources
3. **Creation** - Plugin instances are created with configuration
4. **Initialization** - Plugins are initialized, which includes setting up resources
5. **Usage** - Plugins are used to perform their intended function
6. **Cleanup** - Plugins are cleaned up, which includes releasing resources

### Dependencies

Plugins can depend on other plugins. The dependency system supports:

- **Required Dependencies** - Must be available for the plugin to function
- **Optional Dependencies** - Enhance functionality but are not required
- **Runtime Dependencies** - Needed during runtime but not initialization
- **Enhances Dependencies** - The plugin enhances the functionality of the dependency

The plugin manager automatically handles the dependency resolution and ensures proper initialization and cleanup order.

### Resources

Plugins often need to manage resources like connections, files, or memory. The resource system provides:

- **Resource Pooling** - Shared resources between plugins
- **Lazy Initialization** - Resources are created only when needed
- **Automatic Cleanup** - Resources are properly released when no longer needed

### Extensions

The plugin system supports various extensions:

- **State Persistence** - Preserve plugin state between restarts
- **Hot Reloading** - Update plugins without restarting the application

## Usage Examples

### Basic Plugin Usage

```python
from pepperpy.plugins import create_provider_instance

# Create a plugin instance
llm = create_provider_instance("llm", "openai", api_key="your-api-key")

# Initialize the plugin
await llm.initialize()

# Use the plugin
response = await llm.generate("What is the capital of France?")

# Clean up
await llm.cleanup()
```

### Using Aliases

```python
from pepperpy.plugins import register_plugin_alias, create_provider_instance

# Register an alias for a specific GPT-4 model
register_plugin_alias("llm", "gpt4", "openai", {"model": "gpt-4"})

# Create instance using the alias
llm = create_provider_instance("llm", "gpt4", api_key="your-api-key")

# The model is automatically set to "gpt-4"
```

### Context Manager Pattern

```python
from pepperpy.plugins import auto_context, create_provider_instance

# Create a plugin instance
llm = create_provider_instance("llm", "openai", api_key="your-api-key")

# Use the context manager for automatic cleanup
async with auto_context(llm):
    response = await llm.generate("What is the capital of France?")
```

### Plugin with Dependencies

```python
from pepperpy.plugins import get_plugin_manager

# Get the plugin manager
manager = get_plugin_manager()

# Register plugin metadata with dependencies
manager.register_plugin_metadata("rag", "chroma", {
    "dependencies": [
        {"type": "embeddings", "provider": "openai"},
        {"type": "storage", "provider": "local", "dependency_type": "optional"}
    ]
})

# Create and load the plugin with its dependencies
rag = manager.create_instance("rag", "chroma")
await manager.load_dependencies("rag", "chroma")

# Initialize
await rag.initialize()
```

### Custom Plugin Implementation

```python
from typing import Dict, Any
from pepperpy.plugins import PepperpyPlugin, register_plugin

class CustomPlugin(PepperpyPlugin):
    """Custom plugin implementation."""
    
    # Configuration attributes with defaults
    param1: str = "default"
    param2: int = 42
    
    async def initialize(self):
        """Initialize the plugin."""
        if self.initialized:
            return
            
        self.logger.info(f"Initializing with {self.param1}, {self.param2}")
        self.initialized = True
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data with the plugin."""
        if not self.initialized:
            await self.initialize()
            
        result = {"processed": data, "param1": self.param1}
        return result
        
    async def cleanup(self):
        """Clean up resources."""
        if not self.initialized:
            return
            
        self.logger.info("Cleaning up")
        self.initialized = False

# Register the plugin
register_plugin("custom", "example", CustomPlugin)
```

### Resource Management

```python
from pepperpy.plugins import ResourceMixin, PepperpyPlugin

class ResourcePlugin(PepperpyPlugin, ResourceMixin):
    """Plugin that manages resources."""
    
    async def initialize(self):
        """Initialize the plugin."""
        if self.initialized:
            return
            
        # Get or create a shared database connection
        self.db = await self.get_resource(
            "database",
            factory=self.create_db_connection,
            cleanup=self.close_db_connection
        )
        
        self.initialized = True
        
    async def create_db_connection(self):
        """Create a database connection."""
        self.logger.info("Creating DB connection")
        return {"connection": "db://example"}
        
    async def close_db_connection(self, db):
        """Close a database connection."""
        self.logger.info("Closing DB connection")
```

## Plugin Discovery

The plugin system supports automatic discovery of plugins from various sources:

### Filesystem Discovery

Plugins are discovered from predefined directory structures:

```
plugins/
├── llm/
│   ├── openai/
│   │   ├── plugin.yaml
│   │   └── provider.py
│   └── anthropic/
│       ├── plugin.yaml
│       └── provider.py
└── embeddings/
    ├── openai/
    │   ├── plugin.yaml
    │   └── provider.py
    └── local/
        ├── plugin.yaml
        └── provider.py
```

The `plugin.yaml` file contains metadata:

```yaml
name: OpenAI LLM Provider
version: 1.0.0
description: Provider for OpenAI language models
author: PepperPy Team
license: MIT
entry_point: provider:OpenAIProvider
```

### Default Plugin Paths

The system automatically checks for plugins in these locations:

1. Built-in plugins directory (`pepperpy/plugins`)
2. User config directory (`~/.pepperpy/plugins`)
3. Current working directory (`./plugins`)

### Manual Registration

Plugins can also be registered manually:

```python
from pepperpy.plugins import register_plugin_path

# Register a custom path
register_plugin_path("/path/to/custom/plugins")
```

## Advanced Features

### Fallback Providers

The system supports automatic fallbacks if a requested provider is not available:

```python
from pepperpy.plugins import register_plugin_fallbacks

# Register fallbacks for LLM providers (in order of preference)
register_plugin_fallbacks("llm", ["openai", "anthropic", "local"])
```

### Hot Reloading

The system supports hot reloading of plugins during development:

```python
from pepperpy.plugins import hot_reloadable_plugin, start_hot_reload

# Make a plugin hot-reloadable
@hot_reloadable_plugin
class MyPlugin(PepperpyPlugin):
    pass

# Start hot reload monitoring
start_hot_reload()
```

### State Persistence

Plugins can persist their state between restarts:

```python
from pepperpy.plugins import persistent_plugin

# Make a plugin state persistent
@persistent_plugin
class MyPlugin(PepperpyPlugin):
    # State will be automatically persisted
    counter: int = 0
    
    async def increment(self):
        self.counter += 1
        # Counter will be saved between restarts
```

## Best Practices

1. **Use the Factory Functions**: Prefer `create_provider_instance` over direct instantiation.
2. **Context Managers**: Use `auto_context` for automatic resource cleanup.
3. **Dependency Declaration**: Explicitly declare dependencies in plugin metadata.
4. **Resource Sharing**: Use the `ResourceMixin` for efficient resource sharing.
5. **Aliases for Clarity**: Use aliases for common configurations.
6. **Proper Cleanup**: Always ensure plugins are properly cleaned up.
7. **Type Annotations**: Use type annotations for plugin configuration.
8. **Error Handling**: Handle initialization and cleanup errors gracefully.

## Migration Guide

If you're migrating from an older version of the plugin system, here are the key changes:

1. Use `create_provider_instance` instead of `discovery.create_provider_instance`
2. Use `register_plugin` instead of `core.register_plugin`
3. Use `get_plugin_manager().load_dependencies` instead of manual dependency loading
4. Use the `ResourceMixin` instead of direct resource management

## Troubleshooting

### Common Issues

1. **Plugin Not Found**: Ensure the plugin path is registered and the plugin.yaml file exists.
2. **Initialization Failure**: Check for missing dependencies or configuration.
3. **Circular Dependencies**: Dependency cycles will cause initialization to fail.
4. **Resource Leaks**: Ensure all plugins are properly cleaned up.

### Debugging

Enable debug logging to see more information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support

For more help, refer to the [PepperPy documentation](https://docs.pepperpy.ai) or [file an issue](https://github.com/pimentel/pepperpy/issues). 