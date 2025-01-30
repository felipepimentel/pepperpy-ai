"""
@file: test_config.py
@purpose: Test configuration management system
@component: Tests
@created: 2024-03-20
@task: TASK-001
@status: active
"""

import os
from pathlib import Path
from typing import Generator

from pydantic import ValidationError
import pytest

from pepperpy.common.config import (
    AgentConfig,
    MemoryConfig,
    PepperpyConfig,
    ProviderConfig,
    config,
    initialize_config,
)


@pytest.fixture
def env_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary .env file."""
    env_content = """
    PEPPERPY_ENV=test
    PEPPERPY_DEBUG=true
    PEPPERPY_AGENT_MODEL_TYPE=test-model
    PEPPERPY_MEMORY_EMBEDDING_SIZE=256
    PEPPERPY_PROVIDER_ENABLED_PROVIDERS=["local"]
    """

    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    yield env_file


def test_agent_config_defaults():
    """Test AgentConfig default values."""
    config = AgentConfig()
    assert config.model_type == "gpt-4"
    assert config.temperature == 0.7
    assert config.max_tokens == 1000
    assert config.timeout == 30


def test_memory_config_defaults():
    """Test MemoryConfig default values."""
    config = MemoryConfig()
    assert config.vector_store_type == "faiss"
    assert config.embedding_size == 512
    assert config.cache_ttl == 3600


def test_provider_config_defaults():
    """Test ProviderConfig default values."""
    config = ProviderConfig()
    assert config.enabled_providers == ["openai", "local"]
    assert config.rate_limits == {"openai": 60}


def test_pepperpy_config_defaults():
    """Test PepperpyConfig default values."""
    config = PepperpyConfig()
    assert config.env == "development"
    assert not config.debug
    assert isinstance(config.agent, AgentConfig)
    assert isinstance(config.memory, MemoryConfig)
    assert isinstance(config.provider, ProviderConfig)


def test_config_from_env_file(env_file: Path):
    """Test loading configuration from env file."""
    config = PepperpyConfig.load(env_file)
    assert config.env == "test"
    assert config.debug is True
    assert config.agent.model_type == "test-model"
    assert config.memory.embedding_size == 256
    assert config.provider.enabled_providers == ["local"]


def test_config_validation():
    """Test configuration validation."""
    with pytest.raises(ValidationError):
        AgentConfig(temperature=2.0)  # Invalid temperature

    with pytest.raises(ValidationError):
        MemoryConfig(embedding_size=-1)  # Invalid embedding size

    with pytest.raises(ValidationError):
        ProviderConfig(enabled_providers=123)  # Invalid type


def test_config_override():
    """Test configuration override context manager."""
    config = PepperpyConfig()

    with config.override({"debug": True, "agent": {"model_type": "test"}}):
        assert config.debug is True
        assert config.agent.model_type == "test"

    assert config.debug is False
    assert config.agent.model_type == "gpt-4"


def test_initialize_config(env_file: Path):
    """Test global configuration initialization."""
    initialize_config(env_file)
    assert config.env == "test"
    assert config.debug is True
    assert config.agent.model_type == "test-model"


def test_environment_variables():
    """Test environment variable overrides."""
    os.environ["PEPPERPY_DEBUG"] = "true"
    os.environ["PEPPERPY_AGENT_MODEL_TYPE"] = "env-model"

    config = PepperpyConfig()
    assert config.debug is True
    assert config.agent.model_type == "env-model"

    # Cleanup
    del os.environ["PEPPERPY_DEBUG"]
    del os.environ["PEPPERPY_AGENT_MODEL_TYPE"]
