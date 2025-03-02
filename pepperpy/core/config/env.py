"""Environment management for configuration."""

import os
from typing import Optional

from pepperpy.core.common.config.types import (
    ENV_DEVELOPMENT,
    ENV_PRODUCTION,
    ENV_TEST,
)


class Environment:
    """Environment management for configuration."""

    _current: Optional[str] = None
    _environments = {ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_TEST}

    @classmethod
    def get_current(cls) -> str:
        """Get the current environment.

        Returns:
            str: Current environment name
        """
        if cls._current is None:
            cls._current = os.getenv("PEPPERPY_ENV", ENV_DEVELOPMENT)
            if cls._current not in cls._environments:
                raise ValueError(
                    f"Invalid environment: {cls._current}. "
                    f"Must be one of: {', '.join(sorted(cls._environments))}"
                )
        return cls._current

    @classmethod
    def set_current(cls, env: str) -> None:
        """Set the current environment.

        Args:
            env: Environment name to set

        Raises:
            ValueError: If the environment name is invalid
        """
        if env not in cls._environments:
            raise ValueError(
                f"Invalid environment: {env}. "
                f"Must be one of: {', '.join(sorted(cls._environments))}"
            )
        cls._current = env
        os.environ["PEPPERPY_ENV"] = env

    @classmethod
    def is_development(cls) -> bool:
        """Check if current environment is development."""
        return cls.get_current() == ENV_DEVELOPMENT

    @classmethod
    def is_production(cls) -> bool:
        """Check if current environment is production."""
        return cls.get_current() == ENV_PRODUCTION

    @classmethod
    def is_test(cls) -> bool:
        """Check if current environment is test."""
        return cls.get_current() == ENV_TEST

    @classmethod
    def register(cls, env: str) -> None:
        """Register a new environment.

        Args:
            env: Environment name to register
        """
        cls._environments.add(env)

    @classmethod
    def unregister(cls, env: str) -> None:
        """Unregister an environment.

        Args:
            env: Environment name to unregister

        Raises:
            ValueError: If trying to unregister a built-in environment
        """
        if env in {ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_TEST}:
            raise ValueError(f"Cannot unregister built-in environment: {env}")
        cls._environments.discard(env)

    @classmethod
    def list_environments(cls) -> set[str]:
        """List all registered environments.

        Returns:
            set[str]: Set of registered environment names
        """
        return cls._environments.copy()
