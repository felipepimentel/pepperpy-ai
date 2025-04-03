#!/usr/bin/env python
"""
Minimal example to demonstrate PepperPy configuration system.
"""

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
    config: Dict[str, Any], plugin_type: str, plugin_name: str
) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific plugin.

    Args:
        config: Configuration dictionary
        plugin_type: Plugin type (e.g., 'llm', 'rag')
        plugin_name: Plugin name (e.g., 'openai', 'basic')

    Returns:
        Plugin configuration or None if not found
    """
    if "plugins" not in config:
        return None

    # Check for type/provider structure
    if (
        plugin_type in config["plugins"]
        and plugin_name in config["plugins"][plugin_type]
    ):
        return config["plugins"][plugin_type][plugin_name]

    # Check for direct plugin (no type)
    if plugin_name in config["plugins"]:
        return config["plugins"][plugin_name]

    # Check for namespaced plugins
    for key, value in config["plugins"].items():
        if "." in key and key.split(".", 1)[1] == plugin_name:
            return value

    return None


def is_default_provider(
    config: Dict[str, Any], plugin_type: str, plugin_name: str
) -> bool:
    """Check if a provider is the default for its type.

    Args:
        config: Configuration dictionary
        plugin_type: Plugin type
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


def list_plugins_by_type(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """Group plugins by type.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary mapping plugin types to lists of provider names
    """
    result: Dict[str, List[str]] = {}

    plugins = config.get("plugins", {})
    # In our current config format, all plugins are directly under "plugins"
    # We need to infer the type from context or metadata

    # Special case handling - we know LLM providers
    llm_providers = ["openrouter", "openai", "anthropic"]
    if "llm" not in result:
        result["llm"] = []

    # Special case handling - we know TTS providers
    tts_providers = ["elevenlabs", "murf"]
    if "tts" not in result:
        result["tts"] = []

    # Special case handling - we know RAG providers
    rag_providers = ["basic", "sqlite", "faiss", "chroma"]
    if "rag" not in result:
        result["rag"] = []

    # Special case handling - we know content providers
    content_providers = ["pymupdf"]
    if "content" not in result:
        result["content"] = []

    # Special case handling - we know storage providers
    storage_providers = ["storage.sqlite", "storage.memory"]
    if "storage" not in result:
        result["storage"] = []

    # Special case handling - we know tools providers
    tools_providers = ["github"]
    if "tools" not in result:
        result["tools"] = []

    # Special case handling - we know news providers
    news_providers = ["newsapi"]
    if "news" not in result:
        result["news"] = []

    # Add standalone plugins
    standalone = []

    for plugin_name, plugin_config in plugins.items():
        # Categorize by known types
        if plugin_name in llm_providers:
            result["llm"].append(plugin_name)
        elif plugin_name in tts_providers:
            result["tts"].append(plugin_name)
        elif plugin_name in rag_providers:
            result["rag"].append(plugin_name)
        elif plugin_name in content_providers:
            result["content"].append(plugin_name)
        elif plugin_name in storage_providers:
            result["storage"].append(plugin_name)
        elif plugin_name in tools_providers:
            result["tools"].append(plugin_name)
        elif plugin_name in news_providers:
            result["news"].append(plugin_name)
        # Handle special case for Supabase which has a nested structure
        elif plugin_name == "supabase":
            if "standalone" not in result:
                result["standalone"] = []
            result["standalone"].append(plugin_name)
        # Add as standalone if not categorized
        elif "." in plugin_name:  # Namespaced plugins
            if "community" not in result:
                result["community"] = []
            result["community"].append(plugin_name)
        else:
            standalone.append(plugin_name)

    # Add remaining standalone plugins
    if standalone:
        if "standalone" not in result:
            result["standalone"] = []
        result["standalone"].extend(standalone)

    # Remove empty categories
    return {k: v for k, v in result.items() if v}


def main():
    """Run the example."""
    # Load config
    config = load_config("../config.yaml")

    # Resolve environment variables
    config = resolve_env_vars(config)

    # Print app info
    print(f"App Name: {config.get('app_name', 'Unknown')}")
    print(f"App Version: {config.get('app_version', 'Unknown')}")
    print(f"Debug Mode: {config.get('debug', False)}")

    # Group plugins by type
    plugins_by_type = list_plugins_by_type(config)

    # Print available plugins by type
    if plugins_by_type:
        print("\nAvailable Plugins:")
        for plugin_type, providers in plugins_by_type.items():
            print(f"  {plugin_type}:")
            for provider in providers:
                print(f"    - {provider}")

    # Get specific plugin config (LLM OpenAI)
    openai_config = get_plugin_config(config, "llm", "openai")
    if openai_config:
        print("\nOpenAI LLM Plugin Configuration:")
        for key, value in openai_config.items():
            if key != "key":  # Don't print API key
                print(f"  {key}: {value}")

    # Find default plugins for each type
    print("\nDefault Plugins:")
    for plugin_type, providers in plugins_by_type.items():
        if plugin_type == "standalone":
            continue
        for provider in providers:
            if is_default_provider(config, plugin_type, provider):
                print(f"  {plugin_type}: {provider}")

    # Print usage examples
    print("\nHow to use this config in PepperPy:")
    print(
        """
from pepperpy import PepperPy

# Create a PepperPy instance using config.yaml
pepper = PepperPy()

# Use the default LLM provider (configured in YAML)
async def ask_question():
    async with pepper:
        response = await pepper.ask_query("What is artificial intelligence?")
        print(response)

# Use a specific provider with custom config
async def use_specific_provider():
    pepper.with_llm("openai", model="gpt-4-turbo")
    async with pepper:
        response = await pepper.ask_query("Explain quantum computing")
        print(response)

# All plugin config from YAML is automatically applied
# but can be overridden with specific parameters
"""
    )


if __name__ == "__main__":
    main()
