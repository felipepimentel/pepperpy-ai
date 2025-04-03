#!/usr/bin/env python
"""
Practical example of using YAML configuration for plugins.

This example demonstrates:
1. Loading configuration from YAML
2. Simulating plugin creation with config
3. Implementing fallback mechanisms
4. Showing how to override config values
"""
import asyncio
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class MockPlugin:
    """Mock plugin implementation to demonstrate configuration binding."""

    def __init__(self, plugin_type: str, provider_name: str, **config):
        """Initialize the mock plugin with configuration.

        Args:
            plugin_type: Type of plugin (e.g., "llm", "rag")
            provider_name: Provider name (e.g., "openai", "basic")
            **config: Configuration parameters
        """
        self.plugin_type = plugin_type
        self.provider_name = provider_name
        self.config = config
        self.initialized = False

        # Bind configuration to instance attributes
        for key, value in config.items():
            setattr(self, key, value)

    async def initialize(self) -> None:
        """Initialize the plugin."""
        if self.initialized:
            return

        print(f"Initializing {self.plugin_type}/{self.provider_name} plugin")
        # Simulate initialization delay
        await asyncio.sleep(0.1)
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up plugin resources."""
        if not self.initialized:
            return

        print(f"Cleaning up {self.plugin_type}/{self.provider_name} plugin")
        # Simulate cleanup delay
        await asyncio.sleep(0.1)
        self.initialized = False

    def __str__(self) -> str:
        """String representation of the plugin."""
        config_str = ", ".join(
            [f"{k}={v}" for k, v in self.config.items() if k not in ["key", "api_key"]]
        )
        return f"{self.plugin_type}/{self.provider_name} ({config_str})"


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to the config file

    Returns:
        Loaded configuration dictionary
    """
    # Get absolute path to config file
    config_file = Path(config_path).resolve()

    print(f"Loading config from: {config_file}")

    # Check if config file exists
    if not config_file.exists():
        print(f"Config file not found: {config_file}")
        return {}

    # Load YAML file
    with open(config_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def resolve_env_vars(config: Any) -> Any:
    """Resolve environment variables in config.

    Args:
        config: Configuration to process

    Returns:
        Configuration with environment variables resolved
    """
    if isinstance(config, dict):
        return {key: resolve_env_vars(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [resolve_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith("$"):
        # Extract variable name
        var_name = config[1:]
        return os.environ.get(var_name, config)
    else:
        return config


def get_plugin_config(
    config: Dict[str, Any], plugin_name: str
) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific plugin.

    Args:
        config: Configuration dictionary
        plugin_name: Plugin name

    Returns:
        Plugin configuration or None if not found
    """
    if "plugins" not in config:
        return None

    # Direct lookup
    if plugin_name in config["plugins"]:
        return config["plugins"][plugin_name]

    # Check for namespaced plugins
    for key, value in config["plugins"].items():
        if "." in key and key.split(".", 1)[1] == plugin_name:
            return value

    return None


def get_default_provider(config: Dict[str, Any], plugin_type: str) -> Optional[str]:
    """Get the default provider for a plugin type.

    Args:
        config: Configuration dictionary
        plugin_type: Plugin type

    Returns:
        Default provider name or None if not found
    """
    # Type mappings to identify providers by type
    type_mappings = {
        "llm": ["openrouter", "openai", "anthropic"],
        "tts": ["elevenlabs", "murf"],
        "rag": ["basic", "sqlite", "faiss", "chroma"],
        "content": ["pymupdf"],
    }

    # Check each provider of this type
    for provider in type_mappings.get(plugin_type, []):
        plugin_config = get_plugin_config(config, provider)
        if plugin_config and plugin_config.get("default", False):
            return provider

    return None


async def create_mock_provider(
    config: Dict[str, Any],
    plugin_type: str,
    provider_name: Optional[str] = None,
    **override_config: Any,
) -> MockPlugin:
    """Create a mock provider instance.

    Args:
        config: Configuration dictionary
        plugin_type: Plugin type
        provider_name: Provider name (optional, uses default if not specified)
        **override_config: Configuration overrides

    Returns:
        Mock plugin instance
    """
    # If no provider specified, use default
    if not provider_name:
        provider_name = get_default_provider(config, plugin_type)
        if not provider_name:
            # Fallback to first available provider of this type
            type_mappings = {
                "llm": ["openrouter", "openai", "anthropic"],
                "tts": ["elevenlabs", "murf"],
                "rag": ["basic", "sqlite", "faiss", "chroma"],
                "content": ["pymupdf"],
            }
            for provider in type_mappings.get(plugin_type, []):
                if get_plugin_config(config, provider):
                    provider_name = provider
                    break

    if not provider_name:
        raise ValueError(f"No provider found for plugin type '{plugin_type}'")

    # Get provider configuration
    provider_config = get_plugin_config(config, provider_name) or {}

    # Merge with override configuration
    merged_config = {**provider_config, **override_config}

    # Create the provider instance
    provider = MockPlugin(plugin_type, provider_name, **merged_config)

    # Initialize the provider
    await provider.initialize()

    return provider


async def main():
    """Run the simulated plugin example."""
    print("=== PepperPy YAML Plugin Example ===\n")

    # Load configuration
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = load_config(str(config_path))

    # Resolve environment variables
    config = resolve_env_vars(config)

    # Example 1: Create a provider with default configuration
    print("\n--- Example 1: Creating provider with default configuration ---")
    llm_provider = await create_mock_provider(config, "llm")
    print(f"Created provider: {llm_provider}")

    # Example 2: Create a provider with specific type
    print("\n--- Example 2: Creating provider with specific type ---")
    openai_provider = await create_mock_provider(config, "llm", "openai")
    print(f"Created provider: {openai_provider}")

    # Example 3: Override configuration
    print("\n--- Example 3: Creating provider with configuration override ---")
    custom_provider = await create_mock_provider(
        config, "llm", "openai", model="gpt-4-turbo", temperature=0.9
    )
    print(f"Created provider: {custom_provider}")

    # Example 4: Using a RAG provider
    print("\n--- Example 4: Creating RAG provider ---")
    rag_provider = await create_mock_provider(config, "rag")
    print(f"Created provider: {rag_provider}")

    # Example 5: Show usage with context manager pattern
    print("\n--- Example 5: Usage with context manager pattern ---")

    class ProviderManager:
        def __init__(self, provider: MockPlugin):
            self.provider = provider

        async def __aenter__(self):
            await self.provider.initialize()
            return self.provider

        async def __aexit__(self, *args):
            await self.provider.cleanup()

    # Usage example
    print("Using provider with context manager:")
    async with ProviderManager(custom_provider) as provider:
        # Simulating plugin usage
        print(f"  Using {provider.plugin_type}/{provider.provider_name}")
        print(f"  Model: {provider.model}")
        print(f"  Temperature: {provider.temperature}")

    # Clean up all providers
    print("\nCleaning up resources...")
    await llm_provider.cleanup()
    await openai_provider.cleanup()
    await rag_provider.cleanup()

    print("\nYAML Plugin example completed!")


if __name__ == "__main__":
    asyncio.run(main())
