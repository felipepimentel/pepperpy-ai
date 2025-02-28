"""Environment-specific configuration management."""

from typing import Type

from pepperpy.core.common.config.base import BaseConfig
from pepperpy.core.common.config.environments.development import DevelopmentConfig
from pepperpy.core.common.config.environments.production import ProductionConfig
from pepperpy.core.common.config.environments.test import TestConfig


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
    "DevelopmentConfig",
    "ProductionConfig",
    "TestConfig",
    "get_config",
]
