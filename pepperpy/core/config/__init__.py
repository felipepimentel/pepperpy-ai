"""Configuration management for PepperPy.

This module provides configuration management capabilities for the framework.
"""

# Re-export public interfaces
# Import internal implementations
from pepperpy.core.config.base import BaseConfig
from pepperpy.core.config.development import DevelopmentConfig
from pepperpy.core.config.production import ProductionConfig
from pepperpy.core.config.public import (
    ConfigManager,
    ConfigProvider,
    ConfigSection,
)
from pepperpy.core.config.test import TestConfig


def get_config(environment: str) -> type[BaseConfig]:
    """Get configuration class for environment.

    Args:
        environment: Environment name (development, production, test)

    Returns:
        Configuration class for environment

    Raises:
        ValueError: If environment is invalid
    """
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "test": TestConfig,
    }

    if environment not in configs:
        raise ValueError(
            f"Invalid environment: {environment}. "
            f"Must be one of: {', '.join(configs.keys())}"
        )

    return configs[environment]


__all__ = [
    # Public interfaces
    "ConfigManager",
    "ConfigProvider",
    "ConfigSection",
    # Implementation classes
    "DevelopmentConfig",
    "ProductionConfig",
    "TestConfig",
    "get_config",
]
