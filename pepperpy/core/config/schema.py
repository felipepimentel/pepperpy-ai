"""
Configuration Schema.

This module defines the schema for the PepperPy configuration system,
using Pydantic models to validate configuration and support environment
variable references.
"""

import os
import re
from typing import Any

from pydantic import BaseModel, Field, root_validator, validator

# Regex for environment variable references
ENV_VAR_PATTERN = re.compile(r"\${([A-Za-z0-9_]+)(?::([^}]*))?}")


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
