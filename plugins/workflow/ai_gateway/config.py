#!/usr/bin/env python3
"""
PepperPy AI Gateway Configuration

This module provides configuration management for the AI Gateway,
including loading from files, environment variables, and validation.
"""

import json
import logging
import os
from typing import Any

import yaml

# Default configuration paths
DEFAULT_CONFIG_PATHS = [
    "./ai_gateway.yaml",
    "./ai_gateway.yml",
    "./config/ai_gateway.yaml",
    "./config/ai_gateway.yml",
    "~/.pepperpy/ai_gateway.yaml",
    "~/.pepperpy/ai_gateway.yml",
    "/etc/pepperpy/ai_gateway.yaml",
    "/etc/pepperpy/ai_gateway.yml",
]

# Configuration schema
CONFIG_SCHEMA = {
    "auth": {
        "type": "object",
        "properties": {
            "provider": {"type": "string", "default": "basic"},
            "api_key_header": {"type": "string", "default": "X-API-Key"},
            "api_keys": {"type": "object", "default": {}},
            "require_auth": {"type": "boolean", "default": True},
        },
    },
    "routing": {
        "type": "object",
        "properties": {
            "provider": {"type": "string", "default": "basic"},
            "host": {"type": "string", "default": "0.0.0.0"},
            "port": {"type": "integer", "default": 8080},
            "cors_origins": {"type": "array", "default": ["*"]},
            "log_requests": {"type": "boolean", "default": True},
        },
    },
    "models": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "required": True},
                "provider": {"type": "string", "required": True},
                "model": {"type": "string"},
                "api_key": {"type": "string"},
                "api_base": {"type": "string"},
                "max_tokens": {"type": "integer"},
                "temperature": {"type": "number"},
                "capabilities": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["id", "provider"],
        },
        "default": [],
    },
    "tools": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "required": True},
                "provider": {"type": "string", "required": True},
                "config": {"type": "object"},
            },
            "required": ["id", "provider"],
        },
        "default": [],
    },
    "orchestration": {
        "type": "object",
        "properties": {
            "default_strategy": {"type": "string", "default": "contextual"},
            "fallback_enabled": {"type": "boolean", "default": True},
            "cost_optimization": {"type": "boolean", "default": False},
            "latency_optimization": {"type": "boolean", "default": False},
            "ensemble_methods": {"type": "array", "default": ["first"]},
        },
        "default": {
            "default_strategy": "contextual",
            "fallback_enabled": True,
            "cost_optimization": False,
            "latency_optimization": False,
            "ensemble_methods": ["first"],
        },
    },
    "cache": {
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean", "default": False},
            "ttl": {"type": "integer", "default": 3600},
            "max_size": {"type": "integer", "default": 1000},
        },
        "default": {"enabled": False, "ttl": 3600, "max_size": 1000},
    },
    "logging": {
        "type": "object",
        "properties": {
            "level": {"type": "string", "default": "info"},
            "format": {"type": "string"},
            "file": {"type": "string"},
        },
        "default": {"level": "info"},
    },
}


class ConfigError(Exception):
    """Error in configuration loading or validation."""

    pass


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load configuration from file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        ConfigError: If configuration cannot be loaded
    """
    logger = logging.getLogger("config")

    # If config path specified, only try that one
    if config_path:
        try:
            return _load_config_file(config_path)
        except Exception as e:
            raise ConfigError(f"Error loading config from {config_path}: {e}")

    # Try default paths
    for path in DEFAULT_CONFIG_PATHS:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            try:
                logger.info(f"Loading config from {expanded_path}")
                return _load_config_file(expanded_path)
            except Exception as e:
                logger.warning(f"Error loading config from {expanded_path}: {e}")

    # No config file found, return default config
    logger.info("No config file found, using default configuration")
    return _get_default_config()


def _load_config_file(path: str) -> dict[str, Any]:
    """Load configuration from file.

    Args:
        path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        ConfigError: If configuration cannot be loaded
    """
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")

    try:
        with open(path) as f:
            if path.endswith((".yaml", ".yml")):
                config = yaml.safe_load(f)
            elif path.endswith(".json"):
                config = json.load(f)
            else:
                raise ConfigError(f"Unsupported config file format: {path}")
    except Exception as e:
        raise ConfigError(f"Error reading config file: {e}")

    # Process environment variable references
    config = _process_env_vars(config)

    # Apply defaults
    config = _apply_defaults(config)

    return config


def _process_env_vars(config: dict[str, Any]) -> dict[str, Any]:
    """Process environment variable references in config.

    Replaces values of the form ${ENV_VAR} or $ENV_VAR with the
    value of the corresponding environment variable.

    Args:
        config: Configuration dictionary

    Returns:
        Processed configuration dictionary
    """
    if isinstance(config, dict):
        result = {}
        for key, value in config.items():
            result[key] = _process_env_vars(value)
        return result
    elif isinstance(config, list):
        return [_process_env_vars(item) for item in config]
    elif isinstance(config, str):
        # Check for environment variable reference
        if config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            return os.getenv(env_var, "")
        elif config.startswith("$"):
            env_var = config[1:]
            return os.getenv(env_var, "")
        return config
    else:
        return config


def _get_default_config() -> dict[str, Any]:
    """Get default configuration.

    Returns:
        Default configuration dictionary
    """
    return {
        "auth": {
            "provider": "basic",
            "api_key_header": "X-API-Key",
            "api_keys": {"test-key-1": "user1", "test-key-2": "user2"},
            "require_auth": True,
        },
        "routing": {
            "provider": "basic",
            "host": "0.0.0.0",
            "port": 8080,
            "cors_origins": ["*"],
            "log_requests": True,
        },
        "models": [
            {
                "id": "gpt-3.5-turbo",
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "api_key": "${OPENAI_API_KEY}",
            }
        ],
        "tools": [{"id": "calculator", "provider": "calculator"}],
        "orchestration": {
            "default_strategy": "contextual",
            "fallback_enabled": True,
            "cost_optimization": False,
            "latency_optimization": False,
            "ensemble_methods": ["first"],
        },
        "cache": {"enabled": False, "ttl": 3600, "max_size": 1000},
        "logging": {"level": "info"},
    }


def _apply_defaults(config: dict[str, Any]) -> dict[str, Any]:
    """Apply default values to configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with defaults applied
    """
    result = {}

    # Apply top-level defaults
    for key, schema in CONFIG_SCHEMA.items():
        if key not in config:
            if "default" in schema:
                result[key] = schema["default"]
            else:
                result[key] = {}
        else:
            result[key] = config[key]

    # Apply defaults to auth section
    if "auth" in result:
        auth_schema = CONFIG_SCHEMA["auth"]["properties"]
        for prop, schema in auth_schema.items():
            if prop not in result["auth"] and "default" in schema:
                result["auth"][prop] = schema["default"]

    # Apply defaults to routing section
    if "routing" in result:
        routing_schema = CONFIG_SCHEMA["routing"]["properties"]
        for prop, schema in routing_schema.items():
            if prop not in result["routing"] and "default" in schema:
                result["routing"][prop] = schema["default"]

    # Apply defaults to orchestration section
    if "orchestration" in result:
        orch_schema = CONFIG_SCHEMA["orchestration"]["properties"]
        for prop, schema in orch_schema.items():
            if prop not in result["orchestration"] and "default" in schema:
                result["orchestration"][prop] = schema["default"]

    # Apply defaults to cache section
    if "cache" in result:
        cache_schema = CONFIG_SCHEMA["cache"]["properties"]
        for prop, schema in cache_schema.items():
            if prop not in result["cache"] and "default" in schema:
                result["cache"][prop] = schema["default"]

    # Apply defaults to logging section
    if "logging" in result:
        logging_schema = CONFIG_SCHEMA["logging"]["properties"]
        for prop, schema in logging_schema.items():
            if prop not in result["logging"] and "default" in schema:
                result["logging"][prop] = schema["default"]

    return result


def validate_config(config: dict[str, Any]) -> list[str]:
    """Validate configuration against schema.

    Args:
        config: Configuration dictionary

    Returns:
        List of validation errors
    """
    errors = []

    # Validate required sections
    for key in CONFIG_SCHEMA:
        if key not in config:
            errors.append(f"Missing required section: {key}")

    # Validate auth section
    if "auth" in config:
        auth_schema = CONFIG_SCHEMA["auth"]["properties"]
        for prop in auth_schema:
            if (
                "required" in auth_schema[prop]
                and auth_schema[prop]["required"]
                and prop not in config["auth"]
            ):
                errors.append(f"Missing required auth property: {prop}")

    # Validate routing section
    if "routing" in config:
        routing_schema = CONFIG_SCHEMA["routing"]["properties"]
        for prop in routing_schema:
            if (
                "required" in routing_schema[prop]
                and routing_schema[prop]["required"]
                and prop not in config["routing"]
            ):
                errors.append(f"Missing required routing property: {prop}")

    # Validate models
    if "models" in config and isinstance(config["models"], list):
        for i, model in enumerate(config["models"]):
            if not isinstance(model, dict):
                errors.append(f"Model {i} must be an object")
                continue

            if "id" not in model:
                errors.append(f"Model {i} missing required property: id")

            if "provider" not in model:
                errors.append(f"Model {i} missing required property: provider")

    # Validate tools
    if "tools" in config and isinstance(config["tools"], list):
        for i, tool in enumerate(config["tools"]):
            if not isinstance(tool, dict):
                errors.append(f"Tool {i} must be an object")
                continue

            if "id" not in tool:
                errors.append(f"Tool {i} missing required property: id")

            if "provider" not in tool:
                errors.append(f"Tool {i} missing required property: provider")

    return errors


def setup_logging(config: dict[str, Any]) -> None:
    """Set up logging from configuration.

    Args:
        config: Configuration dictionary
    """
    if "logging" not in config:
        return

    log_config = config["logging"]

    # Get log level
    level_name = log_config.get("level", "info").upper()
    level = getattr(logging, level_name, logging.INFO)

    # Configure logging
    logging.basicConfig(
        level=level,
        format=log_config.get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set up file logging if configured
    if "file" in log_config:
        file_handler = logging.FileHandler(log_config["file"])
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(
                log_config.get(
                    "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
        )

        # Add handler to root logger
        logging.getLogger("").addHandler(file_handler)

    # Log configuration summary
    logger = logging.getLogger("config")
    logger.info(f"Logging initialized at level {level_name}")


def create_config_file(path: str, config: dict[str, Any]) -> None:
    """Create a configuration file.

    Args:
        path: Path to save the configuration file
        config: Configuration dictionary

    Raises:
        ConfigError: If configuration cannot be saved
    """
    path = os.path.expanduser(path)

    # Create directory if it doesn't exist
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(path, "w") as f:
            if path.endswith((".yaml", ".yml")):
                yaml.dump(config, f, default_flow_style=False)
            elif path.endswith(".json"):
                json.dump(config, f, indent=2)
            else:
                raise ConfigError(f"Unsupported config file format: {path}")
    except Exception as e:
        raise ConfigError(f"Error writing config file: {e}")


def get_config_path() -> str | None:
    """Get the path to the active configuration file.

    Returns:
        Path to active configuration file or None if not found
    """
    for path in DEFAULT_CONFIG_PATHS:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            return expanded_path

    return None
