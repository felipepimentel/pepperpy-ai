"""
@file: config.py
@purpose: Core configuration management system
@component: Common
@created: 2024-03-20
@task: TASK-001
@status: active
"""

import contextlib
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, Optional, Type, TypeVar

from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

T = TypeVar("T", bound="BaseConfig")


class BaseConfig(BaseSettings):
    """Base configuration class with environment support."""

    model_config = SettingsConfigDict(
        env_prefix="PEPPERPY_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        validate_assignment=True,
        extra="forbid",
        env_nested_delimiter="__"
    )


class AgentConfig(BaseModel):
    """Agent-specific configuration."""

    model_type: str = "gpt-4"
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(1000, gt=0)
    timeout: int = Field(30, gt=0)

    @classmethod
    def create_default(cls) -> "AgentConfig":
        """Create a default instance."""
        return cls(
            model_type="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            timeout=30
        )


class MemoryConfig(BaseModel):
    """Memory system configuration."""

    vector_store_type: str = "faiss"
    embedding_size: int = Field(512, gt=0)
    cache_ttl: int = Field(3600, gt=0)

    @classmethod
    def create_default(cls) -> "MemoryConfig":
        """Create a default instance."""
        return cls(
            vector_store_type="faiss",
            embedding_size=512,
            cache_ttl=3600
        )


class ProviderConfig(BaseModel):
    """Provider system configuration."""

    enabled_providers: list[str] = ["openai", "local"]
    rate_limits: Dict[str, int] = Field(
        default_factory=lambda: {"openai": 60}
    )

    @classmethod
    def create_default(cls) -> "ProviderConfig":
        """Create a default instance."""
        return cls(
            enabled_providers=["openai", "local"],
            rate_limits={"openai": 60}
        )


class PepperpyConfig(BaseConfig):
    """Root configuration class."""

    # Environment
    env: str = "development"
    debug: bool = False
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent,
        description="Root directory of the project"
    )

    # Components
    agent: AgentConfig = Field(default_factory=AgentConfig.create_default)
    memory: MemoryConfig = Field(default_factory=MemoryConfig.create_default)
    provider: ProviderConfig = Field(default_factory=ProviderConfig.create_default)

    @classmethod
    def load(
        cls: Type[T],
        env_file: Optional[Path] = None,
        **kwargs: Any
    ) -> T:
        """Load configuration from environment and file."""
        try:
            if env_file:
                kwargs["_env_file"] = str(env_file)
            return cls(**kwargs)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}") from e

    @contextlib.contextmanager
    def override(self, overrides: Dict[str, Any]) -> Generator[Any, None, None]:
        """Temporarily override configuration values."""
        original = {}

        try:
            # Save original values
            for key, value in overrides.items():
                if hasattr(self, key):
                    original[key] = getattr(self, key)
                    if isinstance(value, dict) and isinstance(original[key], BaseModel):
                        # Handle nested configuration
                        for subkey, subvalue in value.items():
                            setattr(original[key], subkey, subvalue)
                    else:
                        setattr(self, key, value)

            yield self

        finally:
            # Restore original values
            for key, value in original.items():
                setattr(self, key, value)


# Global configuration instance (lazy initialization)
_config: Optional[PepperpyConfig] = None


def initialize_config(env_file: Optional[Path] = None, **kwargs: Any) -> None:
    """Initialize global configuration."""
    global _config
    _config = PepperpyConfig.load(env_file, **kwargs)


def get_config() -> PepperpyConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = PepperpyConfig()
    return _config

