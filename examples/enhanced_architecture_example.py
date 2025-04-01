"""Enhanced Architecture Example.

This example demonstrates the new architectural capabilities of PepperPy:
- Plugin discovery
- Event system
- Dependency injection
- Centralized configuration
- Unified error handling
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pepperpy import (
    # Core architecture
    init_framework,
    PepperPy,
    BaseProvider,
    
    # DI System
    Container,
    ServiceLifetime,
    get_container,
    inject,
    
    # Plugin system
    PluginInfo,
    create_provider_instance,
    get_plugin_registry,
    
    # Event system
    Event,
    EventBus,
    EventType,
    get_event_bus,
    event_listener,
    
    # Configuration
    Config,
    get_config_registry,
    
    # Logging
    get_logger,
)

# Initialize logger
logger = get_logger("enhanced_example")


# Define a handler for plugin initialization events
@event_listener(EventType.PLUGIN_INITIALIZED)
async def plugin_initialized_handler(data: Dict[str, Any]) -> None:
    """Handle plugin initialization events.
    
    Args:
        data: Event data
    """
    logger.info(
        f"Plugin initialized: {data.get('module')}/{data.get('provider')} - "
        f"Instance: {data.get('instance')}"
    )


# Define a simple service to demonstrate DI
class GreetingService:
    """Service that provides greeting functionality."""
    
    def __init__(self, greeting: Optional[str] = None):
        """Initialize the greeting service.
        
        Args:
            greeting: Optional custom greeting
        """
        self.greeting = greeting or "Hello"
        
    def greet(self, name: str) -> str:
        """Generate a greeting.
        
        Args:
            name: Name to greet
            
        Returns:
            Greeting message
        """
        return f"{self.greeting}, {name}!"


# Define a class that uses DI
class Greeter:
    """Class that uses dependency injection."""
    
    @inject
    def __init__(self, greeting_service: GreetingService):
        """Initialize the greeter.
        
        Args:
            greeting_service: Greeting service (injected)
        """
        self.greeting_service = greeting_service
        
    def greet(self, name: str) -> str:
        """Generate a greeting.
        
        Args:
            name: Name to greet
            
        Returns:
            Greeting message
        """
        return self.greeting_service.greet(name)


async def demonstrate_event_system() -> None:
    """Demonstrate the event system."""
    print("\n=== Event System ===")
    
    # Get the event bus
    event_bus = get_event_bus()
    
    # Define a simple event handler
    async def generic_event_handler(data: Dict[str, Any]) -> None:
        print(f"Event received: {data.get('message', 'No message')}")
    
    # Register the handler
    event_bus.subscribe("demo.event", generic_event_handler)
    
    # Publish an event
    print("Publishing event...")
    await event_bus.publish("demo.event", {"message": "Hello from the event system!"})
    
    # Wait for the event to be processed
    await asyncio.sleep(0.1)


def demonstrate_di_system() -> None:
    """Demonstrate the dependency injection system."""
    print("\n=== Dependency Injection System ===")
    
    # Get the container
    container = get_container()
    
    # Register services
    container.register_instance(
        GreetingService, 
        GreetingService("Greetings")
    )
    
    # Create an instance with DI
    greeter = container.resolve(Greeter)
    
    # Use the instance
    greeting = greeter.greet("PepperPy User")
    print(greeting)


def demonstrate_config_system() -> None:
    """Demonstrate the configuration system."""
    print("\n=== Configuration System ===")
    
    # Get the config registry
    config_registry = get_config_registry()
    
    # Get the core configuration
    core_config = config_registry.get("core")
    
    # Display some configuration values
    print("Core Configuration:")
    print(f"- Environment variables loaded: {len(os.environ)}")
    
    # Create a domain-specific configuration
    demo_config = Config(env_prefix="PEPPERPY_DEMO_")
    demo_config.set("example_key", "example_value")
    
    # Register it
    config_registry.register("demo", demo_config)
    
    # Get it back and use it
    retrieved_config = config_registry.get("demo")
    print(f"Demo config value: {retrieved_config.get('example_key')}")


async def demonstrate_plugin_system() -> None:
    """Demonstrate the plugin system."""
    print("\n=== Plugin System ===")
    
    # Get the plugin registry
    plugin_registry = get_plugin_registry()
    
    # List available plugins
    plugins = plugin_registry.list_plugins()
    categories = plugin_registry.list_categories()
    
    print(f"Found {len(plugins)} plugins in {len(categories)} categories")
    
    if categories:
        # Show plugins by category
        print("\nPlugins by category:")
        for category in categories:
            providers = plugin_registry.list_providers(category)
            if providers:
                print(f"- {category}: {', '.join(providers)}")
    
    # Create a provider instance
    print("\nCreating an LLM provider instance...")
    try:
        # This will trigger our event handler
        llm = create_provider_instance("llm", "openai")
        print(f"Created LLM provider: {llm.__class__.__name__}")
    except Exception as e:
        print(f"Could not create LLM provider: {e}")


async def main() -> None:
    """Main function."""
    print("PepperPy Enhanced Architecture Example")
    print("=" * 50)
    
    # Initialize the framework
    print("\nInitializing the framework...")
    init_framework()
    print("Framework initialized successfully")
    
    # Demonstrate the event system
    await demonstrate_event_system()
    
    # Demonstrate the DI system
    demonstrate_di_system()
    
    # Demonstrate the configuration system
    demonstrate_config_system()
    
    # Demonstrate the plugin system
    await demonstrate_plugin_system()
    
    # Use PepperPy normally
    print("\n=== Using PepperPy ===")
    try:
        async with PepperPy().with_llm() as pepper:
            response = await pepper.chat.with_user("What's new in PepperPy?").generate()
            print("\nChat response:")
            print(response.content)
    except Exception as e:
        print(f"Error using PepperPy: {e}")
    
    print("\nExample completed successfully")


if __name__ == "__main__":
    asyncio.run(main())