"""
@file: test_config.py
@purpose: Tests for configuration management system
@component: Common
@created: 2024-03-20
@task: TASK-001
@status: active
"""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Generator

import pytest
from pydantic import ValidationError

from pepperpy.common.config import (
    AgentConfig,
    MemoryConfig,
    PepperpyConfig,
    ProviderConfig,
    get_config,
    initialize_config,
)

@pytest.fixture
def clean_environment() -> Generator[None, None, None]:
    """Clean environment variables before and after each test."""
    # Save current environment
    old_env = dict(os.environ)
    
    # Clean environment
    for key in list(os.environ.keys()):
        if key.startswith("PEPPERPY_"):
            del os.environ[key]
    
    yield
    
    # Restore environment
    os.environ.clear()
    os.environ.update(old_env)

@pytest.fixture
def test_config() -> PepperpyConfig:
    """Create a test configuration."""
    return PepperpyConfig(
        env="test",
        debug=True,
        agent=AgentConfig(
            model_type="test-model",
            temperature=0.5,
            max_tokens=500,
            timeout=15
        ),
        memory=MemoryConfig(
            vector_store_type="test-store",
            embedding_size=256,
            cache_ttl=1800
        ),
        provider=ProviderConfig(
            enabled_providers=["test"],
            rate_limits={"test": 30}
        )
    )

@pytest.fixture
def env_file() -> Generator[Path, None, None]:
    """Create a temporary .env file."""
    content = """
    PEPPERPY_ENV=test
    PEPPERPY_DEBUG=true
    PEPPERPY_AGENT__MODEL_TYPE=test-model
    PEPPERPY_AGENT__TEMPERATURE=0.5
    PEPPERPY_AGENT__MAX_TOKENS=500
    PEPPERPY_AGENT__TIMEOUT=15
    PEPPERPY_MEMORY__VECTOR_STORE_TYPE=test-store
    PEPPERPY_MEMORY__EMBEDDING_SIZE=256
    PEPPERPY_MEMORY__CACHE_TTL=1800
    PEPPERPY_PROVIDER__ENABLED_PROVIDERS=["test"]
    PEPPERPY_PROVIDER__RATE_LIMITS={"test": 30}
    """
    
    with NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(content)
        env_path = Path(f.name)
    
    yield env_path
    
    # Cleanup
    env_path.unlink()

@pytest.fixture
def initialize_test_config(clean_environment: None) -> None:
    """Initialize test configuration."""
    initialize_config()

def test_agent_config_defaults() -> None:
    """Test default values for AgentConfig."""
    config = AgentConfig.create_default()
    assert config.model_type == "gpt-4"
    assert config.temperature == 0.7
    assert config.max_tokens == 1000
    assert config.timeout == 30

def test_memory_config_defaults() -> None:
    """Test default values for MemoryConfig."""
    config = MemoryConfig.create_default()
    assert config.vector_store_type == "faiss"
    assert config.embedding_size == 512
    assert config.cache_ttl == 3600

def test_provider_config_defaults() -> None:
    """Test default values for ProviderConfig."""
    config = ProviderConfig.create_default()
    assert config.enabled_providers == ["openai", "local"]
    assert config.rate_limits == {"openai": 60}

def test_pepperpy_config_defaults() -> None:
    """Test default values for PepperpyConfig."""
    config = PepperpyConfig()
    assert config.env == "development"
    assert not config.debug
    assert isinstance(config.agent, AgentConfig)
    assert isinstance(config.memory, MemoryConfig)
    assert isinstance(config.provider, ProviderConfig)

def test_config_from_env_file(env_file: Path) -> None:
    """Test loading configuration from .env file."""
    config = PepperpyConfig.load(env_file)
    assert config.env == "test"
    assert config.debug
    assert config.agent.model_type == "test-model"
    assert config.agent.temperature == 0.5
    assert config.agent.max_tokens == 500
    assert config.agent.timeout == 15
    assert config.memory.vector_store_type == "test-store"
    assert config.memory.embedding_size == 256
    assert config.memory.cache_ttl == 1800
    assert config.provider.enabled_providers == ["test"]
    assert config.provider.rate_limits == {"test": 30}

def test_config_validation() -> None:
    """Test configuration validation."""
    with pytest.raises(ValidationError):
        AgentConfig(
            model_type="gpt-4",
            temperature=2.0,  # Invalid temperature
            max_tokens=1000,
            timeout=30
        )
    
    with pytest.raises(ValidationError):
        AgentConfig(
            model_type="gpt-4",
            temperature=0.7,
            max_tokens=-1,  # Invalid max_tokens
            timeout=30
        )
    
    with pytest.raises(ValidationError):
        AgentConfig(
            model_type="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            timeout=0  # Invalid timeout
        )
    
    with pytest.raises(ValidationError):
        MemoryConfig(
            vector_store_type="faiss",
            embedding_size=0,  # Invalid embedding_size
            cache_ttl=3600
        )
    
    with pytest.raises(ValidationError):
        MemoryConfig(
            vector_store_type="faiss",
            embedding_size=512,
            cache_ttl=0  # Invalid cache_ttl
        )

def test_config_override(test_config: PepperpyConfig) -> None:
    """Test configuration override context manager."""
    original_env = test_config.env
    original_debug = test_config.debug
    original_model_type = test_config.agent.model_type
    
    with test_config.override({
        "env": "prod",
        "debug": False,
        "agent": {"model_type": "gpt-3.5-turbo"}
    }):
        assert test_config.env == "prod"
        assert not test_config.debug
        assert test_config.agent.model_type == "gpt-3.5-turbo"
    
    assert test_config.env == original_env
    assert test_config.debug == original_debug
    assert test_config.agent.model_type == original_model_type

def test_initialize_config(env_file: Path) -> None:
    """Test global configuration initialization."""
    initialize_config(env_file)
    config = get_config()
    assert config.env == "test"
    assert config.debug
    assert config.agent.model_type == "test-model"

def test_environment_variables(clean_environment: None) -> None:
    """Test environment variable overrides."""
    os.environ["PEPPERPY_ENV"] = "prod"
    os.environ["PEPPERPY_DEBUG"] = "true"
    os.environ["PEPPERPY_AGENT__MODEL_TYPE"] = "gpt-3.5-turbo"
    
    config = get_config()
    assert config.env == "prod"
    assert config.debug
    assert config.agent.model_type == "gpt-3.5-turbo" 
