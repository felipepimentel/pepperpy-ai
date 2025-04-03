#!/usr/bin/env python
"""
Example showing how to use the PepperPy YAML configuration system.

This example demonstrates:
1. Loading configuration from YAML
2. Accessing plugin configurations 
3. Finding default providers
4. Checking feature flags
"""
import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


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


def get_feature_flag(config: Dict[str, Any], flag_name: str) -> bool:
    """Get the value of a feature flag.

    Args:
        config: Configuration dictionary
        flag_name: Feature flag name

    Returns:
        Feature flag value (True if enabled, False otherwise)
    """
    if "features" not in config:
        return False

    return config["features"].get(flag_name, False)


def list_plugins_by_type(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """Group plugins by type.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary mapping plugin types to lists of provider names
    """
    result: Dict[str, List[str]] = {}

    # Known plugin type mappings
    type_mappings = {
        "llm": ["openrouter", "openai", "anthropic"],
        "tts": ["elevenlabs", "murf"],
        "rag": ["basic", "sqlite", "faiss", "chroma"],
        "content": ["pymupdf"],
        "storage": ["storage.sqlite", "storage.memory"],
        "tools": ["github"],
        "news": ["newsapi"],
    }

    # Initialize categories
    for plugin_type in type_mappings:
        result[plugin_type] = []

    # Add standalone and community categories
    result["standalone"] = []
    result["community"] = []

    plugins = config.get("plugins", {})
    for plugin_name, plugin_config in plugins.items():
        # Categorize by known types
        categorized = False
        for plugin_type, providers in type_mappings.items():
            if plugin_name in providers:
                result[plugin_type].append(plugin_name)
                categorized = True
                break

        # Handle uncategorized plugins
        if not categorized:
            if "." in plugin_name:  # Namespaced plugins
                result["community"].append(plugin_name)
            else:
                result["standalone"].append(plugin_name)

    # Remove empty categories
    return {k: v for k, v in result.items() if v}


def is_default_provider(config: Dict[str, Any], plugin_name: str) -> bool:
    """Check if a provider is the default for its type.

    Args:
        config: Configuration dictionary
        plugin_name: Plugin provider name

    Returns:
        True if the provider is the default, False otherwise
    """
    plugins = config.get("plugins", {})
    if plugin_name in plugins:
        plugin_config = plugins[plugin_name]
        if isinstance(plugin_config, dict):
            return plugin_config.get("default", False)
    return False


async def main():
    """Demonstrate the YAML configuration system."""
    print("=== PepperPy Configuration System Example ===\n")

    # Step 1: Load configuration
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = load_config(str(config_path))

    # Step 2: Resolve environment variables
    config = resolve_env_vars(config)

    # Step 3: Access application info
    print(f"App Name: {config.get('app_name', 'Unknown')}")
    print(f"App Version: {config.get('app_version', 'Unknown')}")
    print(f"Debug Mode: {config.get('debug', False)}")

    # Step 4: Group plugins by type
    plugins_by_type = list_plugins_by_type(config)

    # Step 5: Print available plugins by type
    if plugins_by_type:
        print("\nAvailable Plugins:")
        for plugin_type, providers in plugins_by_type.items():
            print(f"  {plugin_type}:")
            for provider in providers:
                is_default = is_default_provider(config, provider)
                print(f"    - {provider}{' (default)' if is_default else ''}")

    # Step 6: Get plugin configurations
    print("\nPlugin Configurations:")
    for plugin_type, providers in plugins_by_type.items():
        for provider in providers:
            plugin_config = get_plugin_config(config, provider)
            if plugin_config:
                print(f"\n  {plugin_type}/{provider}:")
                # Print non-sensitive config values
                for key, value in plugin_config.items():
                    if key not in ["key", "api_key", "secret"]:
                        print(f"    {key}: {value}")

    # Step 7: Get feature flags
    if "features" in config:
        print("\nFeature Flags:")
        for flag, value in config.get("features", {}).items():
            status = "Enabled" if value else "Disabled"
            print(f"  {flag}: {status}")

    print("\nConfiguration system demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
