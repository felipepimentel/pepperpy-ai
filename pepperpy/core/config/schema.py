"""
Configuration Schema.

This module defines the schema for the PepperPy configuration system,
using Pydantic models to validate configuration and support environment
variable references.
"""

import json
import os
import re
from typing import Any

from pydantic import BaseModel, Field, root_validator, validator

from pepperpy.core.errors import ValidationError
from pepperpy.core.logging import get_logger

try:
    import jsonschema
    from jsonschema import Draft7Validator
    from jsonschema import ValidationError as JsonSchemaValidationError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Regex for environment variable references
ENV_VAR_PATTERN = re.compile(r"\${([A-Za-z0-9_]+)(?::([^}]*))?}")

logger = get_logger(__name__)


class EnvVarReference(BaseModel):
    """Environment variable reference with validation and resolution."""

    env_var: str
    default: str | None = None
    required: bool = False

    @validator("env_var")
    def validate_env_var(cls, v: str) -> str:
        """Validate environment variable name.

        Args:
            v: Environment variable name

        Returns:
            Validated environment variable name

        Raises:
            ValueError: If the environment variable name is invalid
        """
        if not re.match(r"^[A-Za-z0-9_]+$", v):
            raise ValueError(f"Invalid environment variable name: {v}")
        return v

    def resolve(self) -> str | None:
        """Resolve the environment variable value.

        Returns:
            Resolved value or None if not found and not required

        Raises:
            ValueError: If the environment variable is required but not found
        """
        value = os.environ.get(self.env_var, self.default)
        if value is None and self.required:
            raise ValueError(f"Required environment variable {self.env_var} not found")
        return value


class Provider(BaseModel):
    """Provider configuration."""

    type: str
    name: str
    enabled: bool = True
    default: bool = False
    key: EnvVarReference | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    file: str | None = None
    console: bool = True


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str | EnvVarReference
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600


class CacheConfig(BaseModel):
    """Cache configuration."""

    type: str = "memory"
    ttl: int = 3600
    size: int = 1000
    connection_url: str | EnvVarReference | None = None


class SecurityConfig(BaseModel):
    """Security configuration."""

    secret_key: str | EnvVarReference
    algorithm: str = "HS256"
    token_expire_minutes: int = 60
    allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    debug_mode: bool = False


class LLMConfig(BaseModel):
    """LLM configuration."""

    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60


class RAGConfig(BaseModel):
    """RAG configuration."""

    provider: str = "faiss"
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-ada-002"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retriever_k: int = 4
    reranker_enabled: bool = False
    reranker_provider: str | None = None
    reranker_model: str | None = None
    reranker_top_n: int = 3


class TTSConfig(BaseModel):
    """Text to speech configuration."""

    provider: str = "azure"
    voice: str = "en-US-JennyNeural"
    rate: str = "1.0"
    pitch: str = "1.0"
    format: str = "mp3"
    quality: str = "high"


class FeatureFlags(BaseModel):
    """Feature flags configuration."""

    rag_enabled: bool = True
    tts_enabled: bool = False
    stream_responses: bool = True
    trace_enabled: bool = True
    cache_enabled: bool = True
    telemetry_enabled: bool = False
    debug_mode: bool = False


class PluginConfig(BaseModel):
    """Individual plugin configuration that can have any fields."""

    class Config:
        """Allow extra fields for plugin configuration."""

        extra = "allow"


class PluginsConfig(BaseModel):
    """Plugins configuration.

    This is a dictionary of plugin names to their configuration.
    """

    class Config:
        """Allow extra fields for plugins configuration."""

        extra = "allow"


class TemplatesConfig(BaseModel):
    """Templates configuration.

    This is a dictionary of template names to their configuration.
    """

    class Config:
        """Allow extra fields for templates configuration."""

        extra = "allow"


class EnvironmentSpecificConfig(BaseModel):
    """Environment-specific configuration overrides."""

    logging: LoggingConfig | None = None
    database: DatabaseConfig | None = None
    cache: CacheConfig | None = None
    security: SecurityConfig | None = None
    llm: LLMConfig | None = None
    rag: RAGConfig | None = None
    tts: TTSConfig | None = None
    features: FeatureFlags | None = None
    plugins: PluginsConfig | None = None

    class Config:
        """Allow extra fields for environment configuration."""

        extra = "allow"


class DefaultsConfig(BaseModel):
    """Defaults configuration.

    This defines default providers for different domain types.
    """

    llm_provider: str | None = None
    embedding_provider: str | None = None
    tts_provider: str | None = None
    rag_provider: str | None = None
    storage_provider: str | None = None

    class Config:
        """Allow extra fields for defaults configuration."""

        extra = "allow"


class PepperPyConfig(BaseModel):
    """Root configuration model."""

    app_name: str = "PepperPy App"
    version: str = "0.1.0"

    # Core configurations
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig
    database: DatabaseConfig | None = None
    cache: CacheConfig | None = None

    # Feature flags
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    # Domain-specific configurations
    llm: LLMConfig | None = None
    rag: RAGConfig | None = None
    tts: TTSConfig | None = None

    # Provider registry
    providers: list[Provider] = Field(default_factory=list)

    # Default provider configurations
    defaults: DefaultsConfig | None = None

    # Plugins configuration
    plugins: PluginsConfig | None = None

    # Templates for reuse
    templates: TemplatesConfig | None = None

    # Environment-specific overrides
    environments: dict[str, EnvironmentSpecificConfig] = Field(default_factory=dict)

    class Config:
        """Configuration for the model."""

        extra = "allow"  # Allow extra fields

    @root_validator(pre=True)
    def apply_environment_overrides(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Apply environment-specific overrides to configuration.

        This validator checks if we have configuration for the current
        environment and applies any overrides.

        Args:
            values: Configuration values

        Returns:
            Updated configuration values
        """
        # Get current environment
        current_env = os.environ.get("PEPPERPY_ENV", "development")

        # Check if we have configuration for this environment
        environments = values.get("environments", {})
        if not environments or current_env not in environments:
            return values

        # Get environment-specific configuration
        env_config = environments[current_env]
        if not env_config:
            return values

        # Apply overrides from the environment configuration
        for field, value in env_config.items():
            if field.startswith("_"):
                continue

            if value is not None and field in values:
                # Only override fields that exist in the base configuration
                # and have a value in the environment configuration
                values[field] = value

        return values


def resolve_env_references(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Recursively resolve environment variable references in a configuration.

    This function processes strings like "${ENV_VAR:default}" in configuration values.

    Args:
        config_dict: Configuration dictionary

    Returns:
        Configuration with environment variables resolved
    """
    result: dict[str, Any] = {}

    for key, value in config_dict.items():
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            result[key] = resolve_env_references(value)
        elif isinstance(value, list):
            # Process lists
            result[key] = [
                resolve_env_references({str(i): item})[str(i)]
                if isinstance(item, dict)
                else _resolve_env_var_in_string(item)
                if isinstance(item, str)
                else item
                for i, item in enumerate(value)
            ]
        elif isinstance(value, str):
            # Resolve environment variables in strings
            result[key] = _resolve_env_var_in_string(value)
        else:
            # Keep other values as-is
            result[key] = value

    return result


def _resolve_env_var_in_string(value: str) -> str:
    """Resolve environment variables in a string.

    Args:
        value: String value that may contain environment variable references

    Returns:
        String with environment variables resolved
    """
    # Find all environment variable references
    matches = ENV_VAR_PATTERN.findall(value)

    if not matches:
        return value

    result = value

    # Replace each reference with its value
    for var_name, default in matches:
        env_value = os.environ.get(var_name, default)
        if env_value is None:
            env_value = ""

        # Replace the reference with its value
        result = result.replace(
            f"${{{var_name}:{default}}}" if default else f"${{{var_name}}}", env_value
        )

    return result


def load_schema_from_file(schema_path: str) -> dict[str, Any]:
    """Load a JSON schema from a file.

    Args:
        schema_path: Path to the schema file

    Returns:
        Schema as a dictionary

    Raises:
        FileNotFoundError: If schema file not found
        json.JSONDecodeError: If schema is invalid JSON
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path) as f:
        return json.load(f)


class ConfigValidator:
    """Configuration validator using JSON Schema.

    This class provides configuration validation using JSON Schema.
    If jsonschema is not available, a basic validation is performed.
    """

    def __init__(self, schema: dict[str, Any]) -> None:
        """Initialize with schema.

        Args:
            schema: JSON Schema for validation
        """
        self.schema = schema
        self.validator = None

        if HAS_JSONSCHEMA:
            try:
                self.validator = Draft7Validator(schema)
            except Exception as e:
                logger.warning(f"Invalid schema: {e}")

    def validate(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate configuration against schema.

        Args:
            config: Configuration to validate

        Returns:
            Validated configuration with defaults

        Raises:
            ValidationError: If validation fails
        """
        # Use jsonschema if available
        if self.validator:
            try:
                self.validator.validate(config)
            except JsonSchemaValidationError as e:
                path = ".".join([str(p) for p in e.path])
                raise ValidationError(
                    f"Configuration validation failed at {path}: {e.message}"
                )
            return self._apply_defaults(config)

        # Basic validation if jsonschema not available
        return self._basic_validate(config)

    def _basic_validate(self, config: dict[str, Any]) -> dict[str, Any]:
        """Perform basic validation without jsonschema.

        Args:
            config: Configuration to validate

        Returns:
            Validated configuration with defaults

        Raises:
            ValidationError: If validation fails
        """
        # Check required properties
        required = self.schema.get("required", [])
        for prop in required:
            if prop not in config:
                raise ValidationError(f"Missing required property: {prop}")

        # Validate property types
        properties = self.schema.get("properties", {})
        for prop_name, prop_value in config.items():
            if prop_name in properties:
                prop_schema = properties[prop_name]
                self._validate_property(prop_name, prop_value, prop_schema)

        # Apply defaults
        return self._apply_defaults(config)

    def _validate_property(
        self, prop_name: str, prop_value: Any, prop_schema: dict[str, Any]
    ) -> None:
        """Validate a property against its schema.

        Args:
            prop_name: Property name
            prop_value: Property value
            prop_schema: Property schema

        Raises:
            ValidationError: If validation fails
        """
        # Check type
        schema_type = prop_schema.get("type")
        if schema_type == "string" and not isinstance(prop_value, str):
            raise ValidationError(
                f"Property {prop_name} should be a string, got {type(prop_value)}"
            )
        elif schema_type == "number" and not isinstance(prop_value, (int, float)):
            raise ValidationError(
                f"Property {prop_name} should be a number, got {type(prop_value)}"
            )
        elif schema_type == "integer" and not isinstance(prop_value, int):
            raise ValidationError(
                f"Property {prop_name} should be an integer, got {type(prop_value)}"
            )
        elif schema_type == "boolean" and not isinstance(prop_value, bool):
            raise ValidationError(
                f"Property {prop_name} should be a boolean, got {type(prop_value)}"
            )
        elif schema_type == "array" and not isinstance(prop_value, list):
            raise ValidationError(
                f"Property {prop_name} should be an array, got {type(prop_value)}"
            )
        elif schema_type == "object" and not isinstance(prop_value, dict):
            raise ValidationError(
                f"Property {prop_name} should be an object, got {type(prop_value)}"
            )

        # Check enum
        enum_values = prop_schema.get("enum")
        if enum_values and prop_value not in enum_values:
            raise ValidationError(
                f"Property {prop_name} should be one of {enum_values}, got {prop_value}"
            )

    def _apply_defaults(self, config: dict[str, Any]) -> dict[str, Any]:
        """Apply schema defaults to configuration.

        Args:
            config: Configuration to apply defaults to

        Returns:
            Configuration with defaults applied
        """
        # Make a copy to avoid modifying the original
        result = dict(config)

        # Apply defaults from schema
        properties = self.schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if "default" in prop_schema and prop_name not in result:
                result[prop_name] = prop_schema["default"]

        return result


def validate_config(config: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Validate configuration against schema.

    Args:
        config: Configuration to validate
        schema: JSON Schema for validation

    Returns:
        Validated configuration with defaults

    Raises:
        ValidationError: If validation fails
    """
    validator = ConfigValidator(schema)
    return validator.validate(config)


def validate_config_file(config_file: str, schema_file: str) -> dict[str, Any]:
    """Validate configuration file against schema file.

    Args:
        config_file: Path to configuration file
        schema_file: Path to schema file

    Returns:
        Validated configuration with defaults

    Raises:
        FileNotFoundError: If files not found
        ValidationError: If validation fails
    """
    # Load schema
    schema = load_schema_from_file(schema_file)

    # Load config
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(config_file) as f:
        config = json.load(f)

    # Validate
    return validate_config(config, schema)


def merge_configs(
    base_config: dict[str, Any], override_config: dict[str, Any]
) -> dict[str, Any]:
    """Merge two configuration dictionaries.

    Args:
        base_config: Base configuration
        override_config: Configuration to override base

    Returns:
        Merged configuration
    """
    # Start with a copy of the base
    result = dict(base_config)

    # Recursively merge values
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursive merge for nested dictionaries
            result[key] = merge_configs(result[key], value)
        else:
            # Override or add key
            result[key] = value

    return result


class EnvVarResolver:
    """Resolver for environment variables in configuration.

    This class resolves environment variable references in configuration values.
    The format for environment variable references is:

    {
        "api_key": {
            "env_var": "API_KEY",
            "required": true,
            "default": "default_value"
        }
    }
    """

    def __init__(self, config: dict[str, Any], prefix: str = "PEPPERPY_") -> None:
        """Initialize with configuration.

        Args:
            config: Configuration to resolve
            prefix: Environment variable prefix
        """
        self.config = config
        self.prefix = prefix

    def resolve(self) -> dict[str, Any]:
        """Resolve environment variables in configuration.

        Returns:
            Configuration with resolved values

        Raises:
            ValidationError: If required environment variable not found
        """
        # Make a copy to avoid modifying the original
        result = dict(self.config)

        # Process the configuration recursively
        return self._process_dict(result)

    def _process_dict(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Process a dictionary recursively.

        Args:
            config_dict: Dictionary to process

        Returns:
            Processed dictionary

        Raises:
            ValidationError: If required environment variable not found
        """
        result = {}

        for key, value in config_dict.items():
            if isinstance(value, dict):
                if "env_var" in value:
                    # This is an environment variable reference
                    result[key] = self._resolve_env_var(value)
                else:
                    # Recursively process nested dictionaries
                    result[key] = self._process_dict(value)
            elif isinstance(value, list):
                # Process lists
                result[key] = [self._process_value(item) for item in value]
            else:
                # Primitive value, keep as is
                result[key] = value

        return result

    def _process_value(self, value: Any) -> Any:
        """Process a value.

        Args:
            value: Value to process

        Returns:
            Processed value
        """
        if isinstance(value, dict):
            # Recursively process dictionaries
            return self._process_dict(value)
        elif isinstance(value, list):
            # Recursively process lists
            return [self._process_value(item) for item in value]
        else:
            # Primitive value, keep as is
            return value

    def _resolve_env_var(self, env_var_dict: dict[str, Any]) -> Any:
        """Resolve an environment variable reference.

        Args:
            env_var_dict: Environment variable reference

        Returns:
            Resolved value

        Raises:
            ValidationError: If required environment variable not found
        """
        env_var = env_var_dict["env_var"]
        required = env_var_dict.get("required", False)
        default = env_var_dict.get("default")

        # Try with prefix first
        value = os.environ.get(f"{self.prefix}{env_var}")

        # Try without prefix if not found
        if value is None:
            value = os.environ.get(env_var)

        # Handle required variables
        if value is None:
            if required:
                raise ValidationError(
                    f"Required environment variable not found: {env_var}"
                )
            return default

        return value
