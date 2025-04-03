# PepperPy

PepperPy is a flexible Python framework for building AI-powered applications with a plugin-based architecture.

## Features

- **Plugin System**: Extend functionality through custom plugins
- **Service Architecture**: Enable inter-plugin communication through service interfaces
- **Event System**: Use publish/subscribe pattern for loose coupling
- **Provider Management**: Create specialized provider implementations
- **Dependency Injection**: Manage plugin dependencies automatically
- **Resource Management**: Share resources between plugins

## Installation

```bash
pip install pepperpy
```

## Quick Start

```python
import asyncio
from pepperpy import PepperpyPlugin, init_framework, plugin, service, get_logger

logger = get_logger(__name__)

@plugin
class HelloPlugin(PepperpyPlugin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.greeting = kwargs.get("greeting", "Hello")
        
    @service
    def say_hello(self, name: str) -> str:
        message = f"{self.greeting}, {name}!"
        return message

async def main():
    # Initialize framework
    framework = init_framework()
    
    # Create and register plugin
    hello_plugin = HelloPlugin(greeting="Hi")
    framework.register_plugin(hello_plugin)
    
    # Initialize framework
    await framework.initialize()
    await hello_plugin.initialize()
    
    # Use plugin
    message = hello_plugin.say_hello("World")
    logger.info(message)  # Outputs: Hi, World!
    
    # Clean up
    await hello_plugin.cleanup()
    await framework.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## Plugin Types

- **Basic Plugin**: Extend `PepperpyPlugin` for core functionality
- **Provider Plugin**: Extend `ProviderPlugin` for specialized implementations

## Creating Plugins

1. Create a class that extends `PepperpyPlugin` 
2. Use the `@plugin` decorator
3. Implement `initialize()` and `cleanup()` methods
4. Add services with the `@service` decorator

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 