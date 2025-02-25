"""Environment variable configuration provider.

This module provides a configuration provider that loads values from
environment variables.
"""

import os

from pepperpy.core.config.base import ConfigProvider


class EnvironmentProvider(ConfigProvider):
    """Configuration provider that loads values from environment variables.

    This provider maps configuration keys to environment variables using
    a configurable prefix.
    """

    def __init__(self, prefix: str = "PEPPERPY_") -> None:
        """Initialize the provider.

        Args:
            prefix: Prefix for environment variables
        """
        super().__init__()
        self.prefix = prefix

    def _get_env_key(self, key: str) -> str:
        """Get environment variable key.

        Args:
            key: Configuration key

        Returns:
            Environment variable key
        """
        # Convert to uppercase and replace separators
        env_key = key.upper().replace("/", "_").replace(".", "_")
        return f"{self.prefix}{env_key}"

    def _get_config_key(self, env_key: str) -> str:
        """Get configuration key from environment variable key.

        Args:
            env_key: Environment variable key

        Returns:
            Configuration key
        """
        # Remove prefix and convert to lowercase
        key = env_key[len(self.prefix) :].lower()
        return key.replace("_", "/")

    async def get(self, key: str) -> str | None:
        """Get configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value or None if not found
        """
        try:
            env_key = self._get_env_key(key)
            value = os.environ.get(env_key)

            # Record metrics
            self._metrics.counter(
                "config_env_reads",
                1,
                labels={
                    "key": key,
                    "found": str(value is not None).lower(),
                },
            )

            return value

        except Exception as e:
            self._observability.log_error(
                "config.env.get",
                f"Failed to get environment variable: {e}",
                exception=e,
                context={"key": key},
            )
            raise

    async def set(self, key: str, value: str) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value

        Raises:
            NotImplementedError: Setting environment variables is not supported
        """
        raise NotImplementedError("Setting environment variables is not supported")

    async def delete(self, key: str) -> None:
        """Delete configuration value.

        Args:
            key: Configuration key

        Raises:
            NotImplementedError: Deleting environment variables is not supported
        """
        raise NotImplementedError("Deleting environment variables is not supported")

    async def list(self, prefix: str = "") -> list[str]:
        """List configuration keys.

        Args:
            prefix: Optional key prefix to filter by

        Returns:
            List of configuration keys
        """
        try:
            # Get all environment variables with prefix
            keys = []
            for env_key in os.environ:
                if env_key.startswith(self.prefix):
                    key = self._get_config_key(env_key)
                    if key.startswith(prefix):
                        keys.append(key)

            # Record metrics
            self._metrics.gauge(
                "config_env_keys",
                len(keys),
                labels={"prefix": prefix},
            )

            return sorted(keys)

        except Exception as e:
            self._observability.log_error(
                "config.env.list",
                f"Failed to list environment variables: {e}",
                exception=e,
                context={"prefix": prefix},
            )
            raise
