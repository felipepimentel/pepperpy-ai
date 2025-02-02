"""Pytest configuration and fixtures.

This module provides pytest configuration and shared fixtures for all tests.
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from pydantic import SecretStr

from pepperpy.common.config import (
    AgentConfig,
    MemoryConfig,
    PepperpyConfig,
    ProviderConfig,
    initialize_config,
)


@pytest.fixture(autouse=True)
def clean_environment() -> Generator[None, None, None]:
    """Clean environment variables before and after each test."""
    # Store original environment
    original_env = dict(os.environ)

    # Remove Pepperpy environment variables
    for key in list(os.environ.keys()):
        if key.startswith("PEPPERPY_"):
            del os.environ[key]

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_config() -> PepperpyConfig:
    """Create a test configuration."""
    return PepperpyConfig(
        env="test",
        debug=True,
        agent=AgentConfig(
            model_type="test-model", temperature=0.7, max_tokens=1000, timeout=30
        ),
        memory=MemoryConfig(
            vector_store_type="faiss", embedding_size=256, cache_ttl=3600
        ),
        provider=ProviderConfig(
            provider_type="test",
            api_key=SecretStr("test-key"),
            model="test-model",
            max_retries=3,
            timeout=30,
        ),
    )


@pytest.fixture
def env_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary environment file."""
    env_path = tmp_path / ".env"
    env_path.write_text(
        """
PEPPERPY_ENV=test
PEPPERPY_DEBUG=true
PEPPERPY_AGENT__MODEL_TYPE=test-model
PEPPERPY_AGENT__TEMPERATURE=0.7
PEPPERPY_AGENT__MAX_TOKENS=1000
PEPPERPY_AGENT__TIMEOUT=30
PEPPERPY_MEMORY__VECTOR_STORE_TYPE=faiss
PEPPERPY_MEMORY__EMBEDDING_SIZE=256
PEPPERPY_MEMORY__CACHE_TTL=3600
PEPPERPY_PROVIDER__PROVIDER_TYPE=test
PEPPERPY_PROVIDER__API_KEY=test-key
PEPPERPY_PROVIDER__MODEL=test-model
PEPPERPY_PROVIDER__TIMEOUT=30
PEPPERPY_PROVIDER__MAX_RETRIES=3
PEPPERPY_PROVIDER__ENABLED_PROVIDERS='["local"]'
PEPPERPY_PROVIDER__RATE_LIMITS='{"local": 100}'
""".strip()
    )
    yield env_path


@pytest.fixture
def initialize_test_config(env_file: Path, provider_config: ProviderConfig) -> None:
    """Initialize test configuration."""
    initialize_config(env_file=env_file, provider=provider_config)
