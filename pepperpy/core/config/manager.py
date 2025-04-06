"""
Configuration Manager.

This module provides the central configuration management for PepperPy,
integrating YAML configuration with environment variables and providing
a consistent access pattern for all components.
"""

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from pepperpy.core.config.loader import find_config_file, load_yaml_config
from pepperpy.core.config.schema import (
    EnvVarReference,
    PepperPyConfig,
    Provider,
    SecurityConfig,
)
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Global configuration state
_config: PepperPyConfig | None = None
_initialized = False
_security_scan_performed = False

# Constants
API_KEY_PATTERN = re.compile(r"(sk|pk|api-|api_key)[-_][a-zA-Z0-9]{20,}")

# Path to the config file
CONFIG_PATH = os.environ.get("PEPPERPY_CONFIG_PATH", "config.yaml")

# Current environment
ENVIRONMENT = os.environ.get("PEPPERPY_ENV", "development")


def initialize_config(config_path: str | Path | None = None) -> PepperPyConfig:
    """Initialize the configuration system.

    Args:
        config_path: Optional path to configuration file
            If not provided, will search in standard locations

    Returns:
        Loaded and validated configuration

    Raises:
        ConfigurationError: If configuration is invalid or required file not found
    """
    global _config, _initialized

    if _initialized and _config is not None:
        return _config

    # Find config file if not provided
    if config_path is None:
        config_path = find_config_file()
        if config_path is None:
            logger.warning("No configuration file found, using default configuration")
            # Create a minimal valid config with manually constructed EnvVarReference
            secret_key = EnvVarReference(
                env_var="PEPPERPY_SECRET_KEY",
                required=True,
            )
            security_config = SecurityConfig(secret_key=secret_key)

            _config = PepperPyConfig(security=security_config)
            _initialized = True
            return _config

    # Load and validate configuration
    try:
        _config = load_yaml_config(config_path)
        _initialized = True
        logger.info(f"Configuration loaded from {config_path}")

        # Perform security scan
        validate_config_security(_config)

        return _config
    except Exception as e:
        from pepperpy.core.errors import ConfigurationError

        raise ConfigurationError(f"Failed to load configuration: {e!s}") from e


@lru_cache(maxsize=128)
def get_config() -> PepperPyConfig:
    """Get the current configuration.

    Returns:
        Current configuration

    Raises:
        ConfigurationError: If configuration is not initialized
    """
    if not _initialized or _config is None:
        # Auto-initialize with default search paths
        return initialize_config()

    return _config


def get_provider_config(
    provider_type: str, provider_name: str | None = None
) -> Provider | None:
    """Get configuration for a specific provider.

    Args:
        provider_type: Type of provider (e.g., "llm", "tts")
        provider_name: Optional provider name
            If not provided, will return the default provider for the given type

    Returns:
        Provider configuration or None if not found
    """
    config = get_config()

    # Find providers of the requested type
    matching_providers = [
        p for p in config.providers if p.type == provider_type and p.enabled
    ]

    if not matching_providers:
        logger.warning(f"No enabled providers found for type: {provider_type}")
        return None

    # If provider name is specified, find that specific provider
    if provider_name:
        for provider in matching_providers:
            if provider.name == provider_name:
                return provider

        logger.warning(f"Provider not found: {provider_type}/{provider_name}")
        return None

    # Otherwise, find the default provider
    default_providers = [p for p in matching_providers if p.default]
    if default_providers:
        return default_providers[0]

    # If no default is marked, return the first one
    logger.warning(f"No default provider for {provider_type}, using first available")
    return matching_providers[0]


def get_provider_api_key(
    provider_type: str, provider_name: str | None = None
) -> str | None:
    """Get API key for a specific provider.

    Args:
        provider_type: Type of provider (e.g., "llm", "tts")
        provider_name: Optional provider name
            If not provided, will return key for the default provider

    Returns:
        API key or None if not configured
    """
    provider = get_provider_config(provider_type, provider_name)
    if not provider or not provider.key:
        return None

    # The key's value is already resolved by the config system
    if provider.key.env_var:
        return os.environ.get(provider.key.env_var, provider.key.default)

    return None


def get_component_config(component: str) -> dict[str, Any]:
    """Get configuration for a specific component.

    Args:
        component: Component name (e.g., "llm", "tts", "rag")

    Returns:
        Component configuration as dictionary
    """
    config = get_config()

    # Check if this component has moved to the plugins section
    plugin_config = get_plugin_configuration(component)
    if plugin_config:
        # Get component-level config, excluding provider-specific configs
        return {k: v for k, v in plugin_config.items() if not isinstance(v, dict)}

    # Check if the component exists at root level
    if hasattr(config, component):
        component_config = getattr(config, component)
        if component_config:
            # If it's a Pydantic model, convert to dict
            if hasattr(component_config, "dict"):
                return component_config.dict()
            return cast(dict[str, Any], component_config)

    # Return empty config if not found
    logger.warning(f"No configuration found for component: {component}")
    return {}


def get_default_provider(provider_type: str) -> str | None:
    """Get the default provider for a given provider type.

    Args:
        provider_type: Provider type (e.g., "llm", "rag", "tts")

    Returns:
        Default provider name or None if not configured
    """
    config = get_config()

    # Check if we have a defaults section
    if not hasattr(config, "defaults") or config.defaults is None:
        return None

    # Check for the corresponding default provider setting
    defaults = config.defaults
    default_key = f"{provider_type}_provider"

    if isinstance(defaults, dict):
        return defaults.get(default_key)
    elif hasattr(defaults, default_key):
        return getattr(defaults, default_key)

    return None


def get_feature_flag(feature: str) -> bool:
    """Get the value of a feature flag.

    Args:
        feature: Feature flag name

    Returns:
        True if feature is enabled, False otherwise
    """
    config = get_config()

    if not hasattr(config, "features") or config.features is None:
        return False

    features = config.features
    if hasattr(features, feature):
        return getattr(features, feature, False)
    elif isinstance(features, dict):
        return features.get(feature, False)

    return False


def get_environment() -> str:
    """Get the current environment name.

    Returns:
        Environment name (e.g., "development", "production")
    """
    return ENVIRONMENT


def is_development() -> bool:
    """Check if running in development environment.

    Returns:
        True if in development environment, False otherwise
    """
    return get_environment() == "development"


def is_production() -> bool:
    """Check if running in production environment.

    Returns:
        True if in production environment, False otherwise
    """
    return get_environment() == "production"


def get_plugin_configuration(
    plugin_identifier: str, provider_type: str | None = None
) -> dict[str, Any]:
    """Get plugin-specific configuration from the plugins section.

    Args:
        plugin_identifier: Plugin identifier - can be a type (e.g., "rag") or a namespaced name (e.g., "org.plugin")
        provider_type: Optional provider type for typed plugins (e.g., "sqlite", "faiss")

    Returns:
        Plugin configuration dictionary, empty if not found
    """
    config = get_config()
    if not hasattr(config, "plugins") or config.plugins is None:
        return {}

    plugins_dict = getattr(config, "plugins", None)
    if not plugins_dict:
        return {}

    # Convert to dict if it's a Pydantic model
    plugins_dict_data: dict[str, Any] = {}
    if hasattr(plugins_dict, "dict") and not isinstance(plugins_dict, dict):
        plugins_dict_data = plugins_dict.dict()
    else:
        plugins_dict_data = plugins_dict

    # First handle the case of a namespaced plugin (e.g., "org.plugin")
    if "." in plugin_identifier and plugin_identifier in plugins_dict_data:
        plugin_config = plugins_dict_data[plugin_identifier]
        # Apply environment overrides
        plugin_config = apply_environment_overrides(
            plugin_identifier, None, plugin_config
        )
        # Process template references
        plugin_config = process_template_references(plugin_config)
        return resolve_config_references(plugin_config)

    # Handle core domain plugin case
    if plugin_identifier in plugins_dict_data:
        plugin_config = plugins_dict_data[plugin_identifier]

        # If provider_type is specified and exists, return that config
        if (
            provider_type
            and isinstance(plugin_config, dict)
            and provider_type in plugin_config
        ):
            provider_config = plugin_config[provider_type]
            # Apply environment overrides
            provider_config = apply_environment_overrides(
                plugin_identifier, provider_type, provider_config
            )
            # Process template references
            provider_config = process_template_references(provider_config)
            return resolve_config_references(provider_config)

        # If no provider_type or not found, return plugin-level config
        if not provider_type:
            # Apply environment overrides
            plugin_config = apply_environment_overrides(
                plugin_identifier, None, plugin_config
            )
            # Process template references
            plugin_config = process_template_references(plugin_config)
            return resolve_config_references(plugin_config)

    # Return empty dict if nothing found
    return {}


def apply_environment_overrides(
    plugin_type: str, provider_type: str | None, config: dict[str, Any]
) -> dict[str, Any]:
    """Apply environment-specific overrides to plugin configuration.

    Args:
        plugin_type: Plugin type
        provider_type: Optional provider type
        config: Base configuration

    Returns:
        Configuration with environment overrides applied
    """
    # Make a copy to avoid modifying the original
    result = dict(config)

    current_env = get_environment()
    config_obj = get_config()

    # Check if we have environment-specific configurations
    if (
        not hasattr(config_obj, "environments")
        or config_obj.environments is None
        or current_env not in config_obj.environments
    ):
        return result

    # Get current environment configuration
    env_config = config_obj.environments[current_env]

    # Check if the environment has plugin overrides
    if not hasattr(env_config, "plugins") or env_config.plugins is None:
        return result

    env_plugins = env_config.plugins
    if not env_plugins:
        return result

    # Convert to dict if it's a Pydantic model
    env_plugins_data: dict[str, Any] = {}
    if hasattr(env_plugins, "dict") and not isinstance(env_plugins, dict):
        env_plugins_data = env_plugins.dict()
    else:
        env_plugins_data = cast(dict[str, Any], env_plugins)

    # Check if the plugin type exists in environment config
    if plugin_type not in env_plugins_data:
        return result

    plugin_env_config = env_plugins_data[plugin_type]

    # If provider_type is specified, apply provider-specific overrides
    if (
        provider_type
        and isinstance(plugin_env_config, dict)
        and provider_type in plugin_env_config
    ):
        provider_env_config = plugin_env_config[provider_type]
        if isinstance(provider_env_config, dict):
            # Update the result with environment overrides
            result.update(provider_env_config)
    elif isinstance(plugin_env_config, dict) and not provider_type:
        # Apply plugin-level overrides
        result.update(plugin_env_config)

    return result


def process_template_references(config: dict[str, Any]) -> dict[str, Any]:
    """Process template references in configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with templates applied
    """
    # Make a copy to avoid modifying the original
    result = dict(config)

    # Check if there's a template reference
    if "template" in result:
        template_name = result.pop("template")
        template_config = get_template_config(template_name)

        # Merge the template with the config (config values take precedence)
        merged = dict(template_config)
        merged.update(result)
        result = merged

    return result


def get_template_config(template_name: str) -> dict[str, Any]:
    """Get a template configuration.

    Args:
        template_name: Name of the template

    Returns:
        Template configuration dictionary, empty if not found
    """
    config = get_config()
    if not hasattr(config, "templates") or config.templates is None:
        return {}

    templates = config.templates
    if not templates:
        return {}

    # Convert to dict if it's a Pydantic model
    templates_data: dict[str, Any] = {}
    if hasattr(templates, "dict") and not isinstance(templates, dict):
        templates_data = templates.dict()
    else:
        templates_data = cast(dict[str, Any], templates)

    return templates_data.get(template_name, {})


def resolve_config_references(config: dict[str, Any]) -> dict[str, Any]:
    """Resolve variable references in configuration values.

    This function resolves references like "{variable}" in configuration values.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with references resolved
    """
    result = {}

    # Process each key-value pair
    for key, value in config.items():
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            result[key] = resolve_config_references(value)
        elif isinstance(value, str) and "{" in value and "}" in value:
            # Resolve string references
            result[key] = resolve_string_references(value, config)
        else:
            # Keep non-string values as is
            result[key] = value

    return result


def resolve_string_references(value: str, config: dict[str, Any]) -> str:
    """Resolve references in a string value.

    Args:
        value: String value with potential references
        config: Configuration dictionary for reference resolution

    Returns:
        String with references resolved
    """
    # Find all references like {variable}
    pattern = r"\{([^}]+)\}"
    matches = re.findall(pattern, value)

    result = value
    for match in matches:
        if match in config:
            # Replace the reference with its value
            replacement = str(config[match])
            result = result.replace(f"{{{match}}}", replacement)

    return result


def validate_config_security(
    config: PepperPyConfig | None = None,
) -> list[tuple[str, str]]:
    """Validate configuration security.

    This function checks for potential security issues in the configuration,
    such as API keys or secrets included directly in the config file.

    Args:
        config: Configuration to validate, uses current config if None

    Returns:
        List of (path, issue) tuples describing security concerns
    """
    global _security_scan_performed

    if config is None:
        config = get_config()

    issues = []

    # Scan the entire configuration for API keys and secrets
    config_dict = config.dict() if hasattr(config, "dict") else {}
    issues.extend(_scan_dict_for_secrets(config_dict))

    # Log issues if found
    if issues and not _security_scan_performed:
        logger.warning("Security issues found in configuration:")
        for path, issue in issues:
            logger.warning(f"  - {path}: {issue}")

        logger.warning(
            "Please remove sensitive information from your configuration files "
            "and use environment variables instead."
        )

        _security_scan_performed = True

    return issues


def _scan_dict_for_secrets(
    data: dict[str, Any], path: str = ""
) -> list[tuple[str, str]]:
    """Recursively scan a dictionary for secrets.

    Args:
        data: Dictionary to scan
        path: Current path in the config (for reporting)

    Returns:
        List of (path, issue) tuples
    """
    issues = []

    for key, value in data.items():
        current_path = f"{path}.{key}" if path else key

        # Check for API keys in string values
        if isinstance(value, str) and API_KEY_PATTERN.search(value):
            issues.append((
                current_path,
                "Contains what appears to be an API key or secret - use env_var reference instead",
            ))

        # Check if this might be a "default" entry for an API key config
        if key == "default" and isinstance(value, str) and len(value) > 20:
            if current_path.endswith("api_key.default") or current_path.endswith(
                "key.default"
            ):
                issues.append((
                    current_path,
                    "API keys should never have default values in config files",
                ))

        # Recursively scan nested dictionaries
        if isinstance(value, dict):
            issues.extend(_scan_dict_for_secrets(value, current_path))

        # Scan items in lists
        if isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    issues.extend(_scan_dict_for_secrets(item, f"{current_path}[{i}]"))

    return issues


def diagnose_config() -> dict[str, list[str]]:
    """Diagnose configuration issues.

    This function checks for common configuration issues and missing requirements.

    Returns:
        Dictionary of issue categories to lists of issue descriptions
    """
    issues = {
        "security": [],
        "api_keys": [],
        "plugins": [],
        "resources": [],
        "general": [],
    }

    config = get_config()

    # Check for security issues
    security_issues = validate_config_security(config)
    if security_issues:
        for path, issue in security_issues:
            issues["security"].append(f"{path}: {issue}")

    # Check for missing API keys
    for provider in getattr(config, "providers", []):
        if provider.key and provider.key.required:
            api_key = get_provider_api_key(provider.type, provider.name)
            if not api_key:
                issues["api_keys"].append(
                    f"Missing API key for {provider.type}/{provider.name} - "
                    f"Set {provider.key.env_var} environment variable"
                )

    # Check for plugin configuration issues
    plugins_dict = getattr(config, "plugins", {})
    if plugins_dict:
        # Convert to dictionary only if it's a Pydantic model
        plugins_dict_data: dict[str, Any] = {}
        if hasattr(plugins_dict, "dict") and not isinstance(plugins_dict, dict):
            plugins_dict_data = plugins_dict.dict()
        else:
            plugins_dict_data = plugins_dict

        for plugin_type, plugin_config in plugins_dict_data.items():
            if not isinstance(plugin_config, dict):
                continue

            # Check for namespaced plugins
            if "." in plugin_type:
                # No special checks yet for namespaced plugins
                pass
            elif plugin_type in ("llm", "rag", "tts", "storage"):
                # Check if providers actually exist
                for provider_name in plugin_config.keys():
                    provider = get_provider_config(plugin_type, provider_name)
                    if not provider:
                        issues["plugins"].append(
                            f"Configuration for {plugin_type}/{provider_name} exists, "
                            f"but the provider is not registered in the providers section"
                        )

    return issues
