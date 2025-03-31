"""Core interfaces and base classes for PepperPy."""

import abc
import logging
from typing import Any, Dict, List, Optional, TypeVar

# Generic type for configuration values
T = TypeVar("T")


class PepperpyError(Exception):
    """Base class for all PepperPy errors."""

    pass


class ValidationError(PepperpyError):
    """Error raised when validation fails."""

    pass


class ConfigError(PepperpyError):
    """Error in provider configuration."""

    pass


class ProviderError(PepperpyError):
    """Error in provider execution."""

    pass


class BaseProvider(abc.ABC):
    """Base class for PepperPy providers."""

    name: str = "base"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the provider with config options.

        Args:
            **kwargs: Configuration options for the provider
        """
        self._config = dict(kwargs)
        self._metadata: Dict[str, Any] = {}  # Will be populated by subclasses if needed
        self.initialized = False
        # Initialize logger for provider
        self.logger = logging.getLogger(
            f"pepperpy.{self.__class__.__module__}.{self.__class__.__name__}"
        )

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.
        It should initialize any resources needed by the provider.

        Raises:
            ConfigError: If initialization fails due to configuration issues
            ProviderError: If initialization fails due to other issues
        """
        pass

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should be called when the provider is no longer needed.
        It should release any resources used by the provider.

        Raises:
            ProviderError: If cleanup fails
        """
        self.initialized = False

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a string value from config.

        Args:
            key: Config key
            default: Default value if key not found

        Returns:
            String value or default
        """
        value = self._config.get(key)
        if value is None:
            return default
        return str(value)

    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """Get a float value from config.

        Args:
            key: Config key
            default: Default value if key not found

        Returns:
            Float value or default

        Raises:
            ConfigError: If value cannot be converted to float
        """
        value = self._config.get(key)
        if value is None:
            return default

        try:
            return float(value)
        except (ValueError, TypeError) as e:
            raise ConfigError(
                f"Config value '{key}={value}' is not a valid float"
            ) from e

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """Get an integer value from config.

        Args:
            key: Config key
            default: Default value if key not found

        Returns:
            Integer value or default

        Raises:
            ConfigError: If value cannot be converted to int
        """
        value = self._config.get(key)
        if value is None:
            return default

        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise ConfigError(
                f"Config value '{key}={value}' is not a valid integer"
            ) from e

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """Get a boolean value from config.

        Args:
            key: Config key
            default: Default value if key not found

        Returns:
            Boolean value or default
        """
        value = self._config.get(key)
        if value is None:
            return default

        if isinstance(value, bool):
            return value

        # Handle string representations
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ("true", "yes", "1", "y", "on"):
                return True
            if value_lower in ("false", "no", "0", "n", "off"):
                return False

        try:
            return bool(value)
        except (ValueError, TypeError) as e:
            raise ConfigError(
                f"Config value '{key}={value}' is not a valid boolean"
            ) from e

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self._config.get(key, default)

    def validate_config(self, required_keys: List[str]) -> None:
        """Validate provider configuration.

        Args:
            required_keys: List of required configuration keys

        Raises:
            ConfigError: If any required keys are missing
        """
        missing = [key for key in required_keys if key not in self._config]
        if missing:
            raise ConfigError(
                f"Missing required configuration keys: {', '.join(missing)}"
            )

    def update_config(self, **config: Any) -> None:
        """Update provider configuration.

        Args:
            **config: Configuration updates
        """
        self._config.update(config)

    def get_config_with_defaults(
        self, key: str, default: Optional[T] = None
    ) -> Optional[T]:
        """Get a configuration value with fallback to default_config in metadata.

        This method tries to get a value from:
        1. Runtime config (highest priority)
        2. Metadata default_config (if available)
        3. Provided default value (lowest priority)

        Args:
            key: Config key
            default: Default value if no other source is found

        Returns:
            Value from the highest priority source
        """
        # First check runtime config
        if key in self._config:
            return self._config[key]

        # Then check metadata default_config
        if hasattr(self, "_metadata") and self._metadata:
            default_config = self._metadata.get("default_config", {})
            if key in default_config:
                return default_config[key]

        # Finally use provided default
        return default

    def validate_required_config(self) -> None:
        """Validate that all required configuration keys are present.

        Uses metadata.required_config_keys to determine required keys.

        Raises:
            ConfigError: If any required configuration is missing
        """
        if hasattr(self, "_metadata") and self._metadata:
            required_keys = self._metadata.get("required_config_keys", [])
            missing_keys = []

            for key in required_keys:
                value = self.get_config_with_defaults(key)
                if value is None:
                    missing_keys.append(key)

            if missing_keys:
                raise ConfigError(
                    f"Missing required configuration keys: {', '.join(missing_keys)}"
                )

    def _check_initialization(self) -> None:
        """Check if the provider is initialized.

        Raises:
            ConfigError: If the provider is not initialized
        """
        if not self.initialized:
            raise ConfigError(f"{self.__class__.__name__} is not initialized")

    def validate_config_schema(self) -> None:
        """Validate configuration against schema in metadata.

        Uses metadata.config_schema to validate configuration values, including:
        - Required fields
        - Type checking
        - Range validation

        Raises:
            ConfigError: If any configuration value is invalid
        """
        if not hasattr(self, "_metadata") or not self._metadata:
            return

        schema = self._metadata.get("config_schema", {})
        if not schema:
            return

        for key, specs in schema.items():
            # Get value with fallback to default
            value = self.get_config_with_defaults(key)

            # Check required fields
            if specs.get("required", False) and value is None:
                raise ConfigError(f"Missing required configuration key: {key}")

            # Skip further validation if value is None
            if value is None:
                continue

            # Validate type
            value_type = specs.get("type")
            if value_type:
                try:
                    if value_type == "string" and not isinstance(value, str):
                        raise ConfigError(
                            f"Config key '{key}' must be a string, got {type(value).__name__}"
                        )
                    elif value_type == "integer":
                        if not isinstance(value, int) and not (
                            isinstance(value, str) and value.isdigit()
                        ):
                            raise ConfigError(
                                f"Config key '{key}' must be an integer, got {type(value).__name__}"
                            )

                        # Convert to int if string
                        if isinstance(value, str):
                            value = int(value)
                            self._config[key] = value

                        # Check range
                        if "min" in specs and value < specs["min"]:
                            raise ConfigError(
                                f"Config key '{key}' must be at least {specs['min']}, got {value}"
                            )
                        if "max" in specs and value > specs["max"]:
                            raise ConfigError(
                                f"Config key '{key}' must be at most {specs['max']}, got {value}"
                            )

                    elif value_type == "float":
                        if not isinstance(value, (int, float)) and not (
                            isinstance(value, str)
                            and value.replace(".", "", 1).isdigit()
                        ):
                            raise ConfigError(
                                f"Config key '{key}' must be a float, got {type(value).__name__}"
                            )

                        # Convert to float if string or int
                        if not isinstance(value, float):
                            value = float(value)
                            self._config[key] = value

                        # Check range
                        if "min" in specs and value < specs["min"]:
                            raise ConfigError(
                                f"Config key '{key}' must be at least {specs['min']}, got {value}"
                            )
                        if "max" in specs and value > specs["max"]:
                            raise ConfigError(
                                f"Config key '{key}' must be at most {specs['max']}, got {value}"
                            )
                except (ValueError, TypeError) as e:
                    raise ConfigError(
                        f"Invalid value for config key '{key}': {e}"
                    ) from e
