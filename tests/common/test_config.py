"""Configuration tests.

Tests for the configuration management system.
"""

import tempfile
from pathlib import Path

import pytest
from pydantic import SecretStr

from pepperpy.common.config import (
    AgentConfig,
    MemoryConfig,
    PepperpyConfig,
    ProviderConfig,
    get_config,
    initialize_config,
)


@pytest.fixture
def config_file() -> Path:
    """Create a temporary config file.

    Returns:
        Path to temporary config file
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(
            """
agent:
  model_type: gpt-4
  temperature: 0.7
  max_tokens: 100
  timeout: 30

memory:
  vector_store_type: faiss
  embedding_size: 1536
  cache_ttl: 3600

provider:
  provider_type: openai
  api_key: test-key
  model: gpt-4
  max_retries: 3
  timeout: 30
"""
        )
        return Path(f.name)


@pytest.fixture
def agent_config() -> AgentConfig:
    """Create test agent config.

    Returns:
        Test agent config
    """
    return AgentConfig(
        model_type="gpt-4",
        temperature=0.7,
        max_tokens=100,
        timeout=30,
    )


@pytest.fixture
def memory_config() -> MemoryConfig:
    """Create test memory config.

    Returns:
        Test memory config
    """
    return MemoryConfig(
        vector_store_type="faiss",
        embedding_size=1536,
        cache_ttl=3600,
    )


@pytest.fixture
def provider_config() -> ProviderConfig:
    """Create test provider config.

    Returns:
        Test provider config
    """
    return ProviderConfig(
        provider_type="openai",
        api_key=SecretStr("test-key"),
        model="gpt-4",
        timeout=30,
        max_retries=3,
    )


def test_load_config(config_file: Path) -> None:
    """Test loading configuration from file.

    Args:
        config_file: Path to test config file
    """
    initialize_config(env_file=config_file)
    config = get_config()
    assert config is not None
    assert config.agent.temperature == 0.7
    assert config.agent.max_tokens == 100
    assert config.agent.timeout == 30
    assert config.memory.embedding_size == 1536
    assert config.memory.cache_ttl == 3600
    assert config.provider.api_key is not None
    assert config.provider.api_key.get_secret_value() == "test-key"
    assert config.provider.provider_type == "openai"
    assert config.provider.model == "gpt-4"
    assert config.provider.timeout == 30
    assert config.provider.max_retries == 3


def test_load_config_missing_file() -> None:
    """Test loading configuration from missing file."""
    with pytest.raises(FileNotFoundError):
        initialize_config(env_file=Path("nonexistent.yml"))


def test_load_config_invalid_yaml() -> None:
    """Test loading configuration with invalid YAML."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("invalid: yaml: content")
        f.flush()
        with pytest.raises(ValueError):
            initialize_config(env_file=Path(f.name))


def test_reset_config() -> None:
    """Test resetting configuration."""
    config = get_config()
    assert config is not None
    initialize_config()  # Reset to defaults
    new_config = get_config()
    assert new_config is not None


def test_config_validation() -> None:
    """Test configuration validation."""
    with pytest.raises(ValueError):
        AgentConfig(
            model_type="gpt-4",
            temperature=2.0,  # Invalid temperature
            max_tokens=100,
            timeout=30,
        )

    with pytest.raises(ValueError):
        MemoryConfig(
            vector_store_type="faiss",
            embedding_size=-1,  # Invalid embedding size
            cache_ttl=3600,
        )

    with pytest.raises(ValueError):
        ProviderConfig(
            provider_type="openai",
            api_key=SecretStr("test-key"),
            model="gpt-4",
            timeout=0,  # Invalid timeout
            max_retries=3,
        )


def test_config_defaults() -> None:
    """Test configuration defaults."""
    config = PepperpyConfig(
        env="development",
        debug=False,
    )
    assert config.agent.model_type == "gpt-4"
    assert config.agent.temperature == 0.7
    assert config.agent.max_tokens == 1000
    assert config.agent.timeout == 30
    assert config.memory.vector_store_type == "faiss"
    assert config.memory.embedding_size == 512
    assert config.memory.cache_ttl == 3600
    assert config.provider.provider_type == "openai"
    assert config.provider.model == "gpt-3.5-turbo"
    assert config.provider.timeout == 30
    assert config.provider.max_retries == 3
