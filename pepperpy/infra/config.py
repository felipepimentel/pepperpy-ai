"""Configuration validation framework for PepperPy.

This module provides a unified configuration validation framework for PepperPy,
allowing modules to define their configuration schemas and validate configuration
at runtime. This helps ensure that configuration is valid before it's used and
provides clear error messages when configuration is invalid.
"""

import os
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, ValidationError, validator

# Type for configuration dictionaries
ConfigDict = Dict[str, Any]


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        """Initialize the exception.

        Args:
            message: The error message.
            errors: Optional list of specific validation errors.
        """
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a string representation of the exception.

        Returns:
            A string representation of the exception, including the list of errors.
        """
        if not self.errors:
            return self.message

        error_list = "\n".join(f"  - {error}" for error in self.errors)
        return f"{self.message}:\n{error_list}"


class BaseConfig(BaseModel):
    """Base class for configuration models.

    This class provides a base for all configuration models in PepperPy.
    It includes common functionality for loading configuration from
    environment variables and validating configuration.

    Example:
        ```python
        class OpenAIConfig(BaseConfig):
            api_key: str
            model: str = "gpt-4"
            temperature: float = 0.7
            max_tokens: int = 1000

            @validator("temperature")
            def validate_temperature(cls, v):
                if v < 0 or v > 1:
                    raise ValueError("Temperature must be between 0 and 1")
                return v
        ```
    """

    class Config:
        """Pydantic configuration."""

        # Allow extra fields in the configuration
        extra = "allow"
        # Validate assignment to attributes
        validate_assignment = True
        # Use environment variables
        env_prefix = "PEPPERPY_"

    @classmethod
    def from_dict(cls, config_dict: ConfigDict) -> "BaseConfig":
        """Create a configuration model from a dictionary.

        Args:
            config_dict: The configuration dictionary.

        Returns:
            A configuration model instance.

        Raises:
            ConfigValidationError: If the configuration is invalid.
        """
        try:
            return cls(**config_dict)
        except ValidationError as e:
            errors = [f"{error['loc'][0]}: {error['msg']}" for error in e.errors()]
            raise ConfigValidationError(
                f"Invalid configuration for {cls.__name__}", errors
            )

    @classmethod
    def from_env(cls, prefix: Optional[str] = None) -> "BaseConfig":
        """Create a configuration model from environment variables.

        Args:
            prefix: Optional prefix for environment variables. If not provided,
                   the prefix from the Config class will be used.

        Returns:
            A configuration model instance.

        Raises:
            ConfigValidationError: If the configuration is invalid.
        """
        # Get the prefix from the Config class if not provided
        if prefix is None:
            prefix = cls.Config.env_prefix

        # Get the field names from the model
        field_names = []

        # Try different approaches to get field names
        # 1. Try Pydantic v2 model_fields
        if hasattr(cls, "model_fields"):
            field_names = list(cls.model_fields.keys())
        # 2. Try Pydantic v1 __fields__
        elif hasattr(cls, "__fields__") and hasattr(cls.__fields__, "keys"):
            field_names = list(cls.__fields__.keys())
        # 3. Fall back to annotations
        else:
            field_names = list(cls.__annotations__.keys())

        # Create a dictionary of configuration values from environment variables
        config_dict = {}

        for field_name in field_names:
            # Convert field name to uppercase for environment variables
            env_name = f"{prefix}{field_name.upper()}"
            env_value = os.environ.get(env_name)
            if env_value is not None:
                config_dict[field_name] = env_value

        # Create the configuration model from the dictionary
        return cls.from_dict(config_dict)

    def to_dict(self) -> ConfigDict:
        """Convert the configuration model to a dictionary.

        Returns:
            A dictionary representation of the configuration model.
        """
        return self.dict()

    @classmethod
    def validate(cls, value: Any) -> "BaseConfig":
        """Validate the configuration.

        Args:
            value: The value to validate.

        Returns:
            A validated configuration model.

        Raises:
            ConfigValidationError: If validation fails.
        """
        try:
            if isinstance(value, dict):
                return cls(**value)
            elif isinstance(value, cls):
                return value
            else:
                raise ConfigValidationError(
                    f"Expected dict or {cls.__name__}, got {type(value).__name__}"
                )
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {str(e)}")


class ConfigRegistry:
    """Registry for configuration models.

    This class provides a registry for configuration models, allowing modules
    to register their configuration schemas and retrieve configuration instances.

    Example:
        ```python
        # Register a configuration model
        ConfigRegistry.register("openai", OpenAIConfig)

        # Get a configuration instance
        config = ConfigRegistry.get_config("openai")
        ```
    """

    _registry: Dict[str, Type[BaseConfig]] = {}
    _instances: Dict[str, BaseConfig] = {}

    @classmethod
    def register(cls, name: str, config_class: Type[BaseConfig]) -> None:
        """Register a configuration model.

        Args:
            name: The name of the configuration model.
            config_class: The configuration model class.
        """
        cls._registry[name] = config_class

    @classmethod
    def get_config_class(cls, name: str) -> Type[BaseConfig]:
        """Get a configuration model class.

        Args:
            name: The name of the configuration model.

        Returns:
            The configuration model class.

        Raises:
            KeyError: If the configuration model is not registered.
        """
        if name not in cls._registry:
            raise KeyError(f"Configuration model '{name}' is not registered")
        return cls._registry[name]

    @classmethod
    def get_config(cls, name: str) -> BaseConfig:
        """Get a configuration instance.

        This method returns a configuration instance for the given name.
        If an instance doesn't exist, it will be created from environment
        variables.

        Args:
            name: The name of the configuration model.

        Returns:
            A configuration instance.

        Raises:
            KeyError: If the configuration model is not registered.
            ConfigValidationError: If the configuration is invalid.
        """
        if name not in cls._instances:
            config_class = cls.get_config_class(name)
            cls._instances[name] = config_class.from_env()
        return cls._instances[name]

    @classmethod
    def set_config(cls, name: str, config: Union[BaseConfig, ConfigDict]) -> None:
        """Set a configuration instance.

        Args:
            name: The name of the configuration model.
            config: The configuration instance or dictionary.

        Raises:
            KeyError: If the configuration model is not registered.
            ConfigValidationError: If the configuration is invalid.
        """
        config_class = cls.get_config_class(name)
        if isinstance(config, dict):
            config = config_class.from_dict(config)
        elif not isinstance(config, config_class):
            raise TypeError(
                f"Expected {config_class.__name__} or dict, got {type(config).__name__}"
            )
        cls._instances[name] = config

    @classmethod
    def reset(cls, name: Optional[str] = None) -> None:
        """Reset the configuration registry.

        Args:
            name: Optional name of the configuration model to reset.
                 If not provided, all configuration instances will be reset.
        """
        if name is None:
            cls._instances.clear()
        elif name in cls._instances:
            del cls._instances[name]


# Common configuration models


class LoggingConfig(BaseConfig):
    """Configuration for logging.

    Attributes:
        level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format: The logging format string.
        file: Optional path to a log file.
    """

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None

    @validator("level")
    def validate_level(cls, v: str) -> str:
        """Validate the logging level.

        Args:
            v: The logging level.

        Returns:
            The validated logging level.

        Raises:
            ValueError: If the logging level is invalid.
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid logging level: {v}. Must be one of {valid_levels}"
            )
        return v.upper()


class APIKeyConfig(BaseConfig):
    """Configuration for API keys.

    Attributes:
        openai: Optional OpenAI API key.
        anthropic: Optional Anthropic API key.
        pinecone: Optional Pinecone API key.
        cohere: Optional Cohere API key.
    """

    openai: Optional[str] = None
    anthropic: Optional[str] = None
    pinecone: Optional[str] = None
    cohere: Optional[str] = None


class GlobalConfig(BaseConfig):
    """Global configuration for PepperPy.

    Attributes:
        default_llm_provider: The default LLM provider to use.
        default_rag_provider: The default RAG provider to use.
        default_data_provider: The default data provider to use.
        api_keys: Configuration for API keys.
        logging: Configuration for logging.
    """

    default_llm_provider: str = "openai"
    default_rag_provider: str = "basic"
    default_data_provider: str = "memory"
    api_keys: APIKeyConfig = Field(default_factory=APIKeyConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


# Register common configuration models
ConfigRegistry.register("global", GlobalConfig)
ConfigRegistry.register("logging", LoggingConfig)
ConfigRegistry.register("api_keys", APIKeyConfig)


# Convenience functions


def get_config(name: str) -> BaseConfig:
    """Get a configuration instance.

    Args:
        name: The name of the configuration model.

    Returns:
        A configuration instance.

    Raises:
        KeyError: If the configuration model is not registered.
        ConfigValidationError: If the configuration is invalid.
    """
    return ConfigRegistry.get_config(name)


def set_config(name: str, config: Union[BaseConfig, ConfigDict]) -> None:
    """Set a configuration instance.

    Args:
        name: The name of the configuration model.
        config: The configuration instance or dictionary.

    Raises:
        KeyError: If the configuration model is not registered.
        ConfigValidationError: If the configuration is invalid.
    """
    ConfigRegistry.set_config(name, config)


def register_config(name: str, config_class: Type[BaseConfig]) -> None:
    """Register a configuration model.

    Args:
        name: The name of the configuration model.
        config_class: The configuration model class.
    """
    ConfigRegistry.register(name, config_class)


def reset_config(name: Optional[str] = None) -> None:
    """Reset the configuration registry.

    Args:
        name: Optional name of the configuration model to reset.
             If not provided, all configuration instances will be reset.
    """
    ConfigRegistry.reset(name)
