"""Configuration schema for PepperPy YAML configuration.

This module defines the schema structure and validation for the PepperPy YAML configuration
system, including support for environment variable references.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, root_validator, validator


class EnvVarReference(BaseModel):
    """Environment variable reference with fallback support."""

    env_var: str
    default: Optional[str] = None
    required: bool = False

    @validator("env_var")
    def validate_env_var(cls, v: str) -> str:
        """Validate environment variable name."""
        if not v:
            raise ValueError("Environment variable name cannot be empty")
        return v

    def resolve(self) -> Optional[str]:
        """Resolve environment variable value with fallback to default."""
        value = os.environ.get(self.env_var, self.default)
        if value is None and self.required:
            raise ValueError(f"Required environment variable {self.env_var} not set")
        return value


class Provider(BaseModel):
    """Provider configuration model."""

    type: str
    name: str
    default: bool = False
    enabled: bool = True
    key: Optional[EnvVarReference] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    for_tasks: Optional[List[str]] = None

    class Config:
        """Pydantic config."""

        extra = "allow"


class LoggingConfig(BaseModel):
    """Logging configuration model."""

    level: str = "INFO"
    format: str = "console"
    file: Optional[str] = None
    max_size: Optional[int] = None
    backup_count: Optional[int] = None


class DatabaseConfig(BaseModel):
    """Database configuration model."""

    url: EnvVarReference
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False


class CacheConfig(BaseModel):
    """Cache configuration model."""

    enabled: bool = True
    backend: str = "disk"
    ttl: int = 3600
    max_size: Optional[int] = None
    path: Optional[str] = None
    redis_uri: Optional[EnvVarReference] = None


class SecurityConfig(BaseModel):
    """Security configuration model."""

    secret_key: EnvVarReference
    api_key: Optional[EnvVarReference] = None
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    allow_headers: List[str] = Field(default_factory=lambda: ["*"])


class LLMConfig(BaseModel):
    """LLM configuration model."""

    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60
    retries: int = 3


class RAGConfig(BaseModel):
    """RAG configuration model."""

    provider: str = "basic"
    embedding_provider: str = "openai"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    similarity_top_k: int = 4
    vector_store: str = "memory"


class TTSConfig(BaseModel):
    """TTS configuration model."""

    provider: str = "elevenlabs"
    voice: Optional[str] = None
    output_format: str = "mp3"
    cache_enabled: bool = True


class FeatureFlags(BaseModel):
    """Feature flags configuration model."""

    enable_telemetry: bool = False
    enable_cache: bool = True
    enable_auto_discovery: bool = True
    enable_hot_reload: bool = False


class EnvironmentSpecificConfig(BaseModel):
    """Environment-specific configuration that can override base settings."""

    logging: Optional[LoggingConfig] = None
    database: Optional[DatabaseConfig] = None
    cache: Optional[CacheConfig] = None
    security: Optional[SecurityConfig] = None
    llm: Optional[LLMConfig] = None
    rag: Optional[RAGConfig] = None
    tts: Optional[TTSConfig] = None
    features: Optional[FeatureFlags] = None
    providers: Optional[List[Provider]] = None


class PepperPyConfig(BaseModel):
    """Root configuration model for PepperPy."""

    # Core configurations
    app_name: str = "PepperPy"
    app_version: str = "0.1.0"
    debug: bool = False

    # Component configurations
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    database: Optional[DatabaseConfig] = None
    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig
    llm: LLMConfig = Field(default_factory=LLMConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)

    # Feature flags
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    # Provider configurations
    providers: List[Provider] = Field(default_factory=list)

    # Environment-specific configurations
    environments: Dict[str, EnvironmentSpecificConfig] = Field(default_factory=dict)

    @root_validator(pre=True)
    def validate_environment_configs(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Apply current environment configuration if available."""
        env = os.environ.get("PEPPERPY_ENV", "development")
        env_config = values.get("environments", {}).get(env)
        
        if env_config:
            for field, env_value in env_config.dict(exclude_unset=True).items():
                if field in values and isinstance(env_value, dict) and isinstance(values[field], dict):
                    # Merge dictionaries for nested configs
                    values[field].update(env_value)
                elif field in values:
                    # Replace value
                    values[field] = env_value
        
        return values

    class Config:
        """Pydantic config."""

        extra = "allow"


def resolve_env_references(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively resolve environment variable references in a configuration dictionary.

    Args:
        config_dict: Dictionary potentially containing environment variable references

    Returns:
        Dictionary with resolved values
    """
    result = {}

    for key, value in config_dict.items():
        if isinstance(value, dict):
            if "env_var" in value and isinstance(value.get("env_var"), str):
                # This looks like an EnvVarReference
                ref = EnvVarReference(**value)
                result[key] = ref.resolve()
            else:
                # Regular nested dictionary
                result[key] = resolve_env_references(value)
        elif isinstance(value, list):
            # Process lists
            result[key] = [
                resolve_env_references(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            # Regular value
            result[key] = value

    return result


def load_yaml_config(file_path: Union[str, Path]) -> PepperPyConfig:
    """Load and validate YAML configuration file.

    Args:
        file_path: Path to YAML configuration file

    Returns:
        Validated PepperPyConfig instance

    Raises:
        FileNotFoundError: If configuration file doesn't exist
        ValueError: If configuration is invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    # Load YAML file
    with open(path) as f:
        yaml_dict = yaml.safe_load(f)

    # Resolve environment variables
    resolved_dict = resolve_env_references(yaml_dict)

    # Validate against schema
    return PepperPyConfig(**resolved_dict)


def find_config_file() -> Optional[Path]:
    """Find configuration file in standard locations.

    Checks for config.yaml in the following locations:
    1. Current directory
    2. ~/.pepperpy/
    3. /etc/pepperpy/

    Returns:
        Path to configuration file or None if not found
    """
    # Search paths in order of priority
    search_paths = [
        Path.cwd() / "config.yaml",
        Path.cwd() / "pepperpy.yaml",
        Path.home() / ".pepperpy" / "config.yaml",
        Path("/etc/pepperpy/config.yaml"),
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None
