"""Configuration management for Pepperpy.

This module handles configuration loading and validation for the Pepperpy framework.
It supports loading from environment variables and configuration files.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from pepperpy.monitoring import logger


class AutoConfig(BaseModel):
    """Automatic configuration from environment variables.

    This class automatically loads and validates configuration from environment
    variables, providing sensible defaults when possible.

    Environment Variables:
        PEPPERPY_API_KEY: Primary API key
        PEPPERPY_PROVIDER: Provider type (default: openrouter)
        PEPPERPY_MODEL: Model name (default: google/gemini-2.0-flash-exp:free)
        PEPPERPY_FALLBACK_API_KEY: Fallback API key (optional)
        PEPPERPY_FALLBACK_PROVIDER: Fallback provider type (optional)
        PEPPERPY_FALLBACK_MODEL: Fallback model name (optional)
    """

    # Primary provider settings
    api_key: SecretStr
    provider_type: str = Field(default="openrouter")
    model: str = Field(default="google/gemini-2.0-flash-exp:free")

    # Fallback provider settings
    fallback_api_key: SecretStr | None = None
    fallback_provider_type: str | None = None
    fallback_model: str | None = None

    # Common settings
    max_retries: int = Field(default=3)
    timeout: int = Field(default=30)

    @classmethod
    def from_env(cls, load_dotenv_file: bool = True) -> "AutoConfig":
        """Create configuration from environment variables.

        Args:
            load_dotenv_file: Whether to load .env file if present

        Returns:
            AutoConfig: Configured instance

        Raises:
            ValueError: If required environment variables are missing
        """
        if load_dotenv_file:
            load_dotenv()

        # Get required primary API key
        api_key = os.getenv("PEPPERPY_API_KEY")
        if not api_key:
            raise ValueError("PEPPERPY_API_KEY environment variable is required")

        # Get optional settings with defaults
        provider_type = os.getenv("PEPPERPY_PROVIDER", "openrouter")
        model = os.getenv("PEPPERPY_MODEL", "google/gemini-2.0-flash-exp:free")

        # Get optional fallback settings
        fallback_api_key = os.getenv("PEPPERPY_FALLBACK_API_KEY")
        fallback_provider = os.getenv("PEPPERPY_FALLBACK_PROVIDER")
        fallback_model = os.getenv("PEPPERPY_FALLBACK_MODEL")

        return cls(
            api_key=SecretStr(api_key),
            provider_type=provider_type,
            model=model,
            fallback_api_key=SecretStr(fallback_api_key) if fallback_api_key else None,
            fallback_provider_type=fallback_provider,
            fallback_model=fallback_model,
        )

    def get_provider_config(self, is_fallback: bool = False) -> "ProviderConfig":
        """Convert to ProviderConfig for provider initialization.

        Args:
            is_fallback: Whether to return fallback configuration

        Returns:
            ProviderConfig: Configuration for provider initialization

        Raises:
            ValueError: If trying to get fallback config when not configured
        """
        if is_fallback and not self.fallback_api_key:
            raise ValueError("Fallback provider not configured")

        return ProviderConfig(
            provider_type=self.fallback_provider_type
            if is_fallback
            else self.provider_type,
            api_key=self.fallback_api_key if is_fallback else self.api_key,
            model=self.fallback_model if is_fallback else self.model,
            max_retries=self.max_retries,
            timeout=self.timeout,
        )


class AgentConfig(BaseModel):
    """Agent configuration."""

    model_type: str = "gpt-4"
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1000, gt=0)
    timeout: int = Field(default=30, gt=0)

    @classmethod
    def create_default(cls) -> "AgentConfig":
        """Create default agent configuration."""
        return cls()


class MemoryConfig(BaseModel):
    """Memory configuration."""

    vector_store_type: str = "faiss"
    embedding_size: int = Field(default=512, gt=0)
    cache_ttl: int = Field(default=3600, gt=0)

    @classmethod
    def create_default(cls) -> "MemoryConfig":
        """Create default memory configuration."""
        return cls()


class ProviderConfig(BaseModel):
    """Provider configuration."""

    provider_type: str = "openai"
    api_key: SecretStr | None = None
    model: str = "gpt-3.5-turbo"
    timeout: int = Field(default=30, gt=0)
    max_retries: int = Field(default=3, ge=0)
    enabled_providers: list[str] = Field(default_factory=list)
    rate_limits: dict[str, int] = Field(default_factory=dict)

    @classmethod
    def create_default(cls) -> "ProviderConfig":
        """Create default provider configuration."""
        return cls()


class PepperpyConfig(BaseSettings):
    """Global Pepperpy configuration."""

    model_config = SettingsConfigDict(
        env_prefix="PEPPERPY_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )

    env: str = "development"
    debug: bool = False
    agent: AgentConfig = Field(default_factory=AgentConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    provider: ProviderConfig = Field(default_factory=ProviderConfig)

    @classmethod
    def create_default(cls) -> "PepperpyConfig":
        """Create default configuration."""
        return cls(
            env="development",
            debug=False,
            agent=AgentConfig.create_default(),
            memory=MemoryConfig.create_default(),
            provider=ProviderConfig.create_default(),
        )


_config: PepperpyConfig | None = None


def initialize_config(env_file: Path | None = None, **kwargs: Any) -> None:
    """Initialize global configuration."""
    global _config
    try:
        if env_file:
            if not env_file.exists():
                raise FileNotFoundError(f"Config file not found: {env_file}")

            try:
                with open(env_file) as f:
                    config_data = yaml.safe_load(f)
                    if not isinstance(config_data, dict):
                        raise ValueError("Invalid YAML: root must be a mapping")

                    # Convert each section
                    config_settings: dict[str, Any] = {}

                    # Convert agent config
                    if "agent" in config_data:
                        agent_config = config_data["agent"]
                        if not isinstance(agent_config, dict):
                            raise ValueError(
                                "Invalid YAML: agent section must be a mapping"
                            )
                        config_settings["agent"] = AgentConfig(
                            model_type=str(agent_config.get("model_type", "gpt-4")),
                            temperature=float(agent_config.get("temperature", 0.7)),
                            max_tokens=int(agent_config.get("max_tokens", 1000)),
                            timeout=int(agent_config.get("timeout", 30)),
                        )

                    # Convert memory config
                    if "memory" in config_data:
                        memory_config = config_data["memory"]
                        if not isinstance(memory_config, dict):
                            raise ValueError(
                                "Invalid YAML: memory section must be a mapping"
                            )
                        config_settings["memory"] = MemoryConfig(
                            vector_store_type=str(
                                memory_config.get("vector_store_type", "faiss")
                            ),
                            embedding_size=int(
                                memory_config.get("embedding_size", 512)
                            ),
                            cache_ttl=int(memory_config.get("cache_ttl", 3600)),
                        )

                    # Convert provider config
                    if "provider" in config_data:
                        provider_config = config_data["provider"]
                        if not isinstance(provider_config, dict):
                            raise ValueError(
                                "Invalid YAML: provider section must be a mapping"
                            )

                        provider_settings: dict[str, Any] = {}
                        for key, value in provider_config.items():
                            if key == "api_key":
                                provider_settings[key] = SecretStr(str(value))
                            elif key == "enabled_providers":
                                if isinstance(value, list):
                                    provider_settings[key] = [str(v) for v in value]
                                else:
                                    provider_settings[key] = [
                                        v.strip() for v in str(value).split(",")
                                    ]
                            elif key == "rate_limits":
                                if isinstance(value, dict):
                                    provider_settings[key] = {
                                        str(k): int(v) for k, v in value.items()
                                    }
                                else:
                                    provider_settings[key] = {
                                        k.strip(): int(v.strip())
                                        for pair in str(value).split(",")
                                        for k, v in [pair.split(":")]
                                    }
                            elif key in ["max_retries", "timeout"]:
                                provider_settings[key] = int(value)
                            else:
                                provider_settings[key] = str(value)

                        config_settings["provider"] = ProviderConfig(
                            **provider_settings
                        )

                    # Initialize root config with all sections
                    _config = PepperpyConfig(**{**config_settings, **kwargs})

            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in config file: {e}") from e
            except Exception as e:
                if isinstance(e, FileNotFoundError):
                    raise
                raise ValueError(f"Failed to parse config file: {e}") from e
        else:
            # Initialize with defaults if no file provided
            _config = PepperpyConfig(**kwargs)

    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to initialize config", error=str(e))
        # If initialization fails for other reasons, create a default configuration
        _config = PepperpyConfig.create_default()
        raise


def get_config() -> PepperpyConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        initialize_config()
    assert _config is not None  # For type checker
    return _config
