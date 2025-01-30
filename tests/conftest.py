"""
@file: conftest.py
@purpose: Pytest configuration and fixtures
@component: Tests
@created: 2024-03-20
@task: TASK-001
@status: active
"""

import os
from pathlib import Path
from typing import Generator

import pytest

from pepperpy.common.config import PepperpyConfig, initialize_config


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
        agent={"model_type": "test-model"},
        memory={"embedding_size": 256},
        provider={"enabled_providers": ["local"]},
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


@pytest.fixture(autouse=True)
def initialize_test_config(clean_environment: None) -> None:
    """Initialize test configuration."""
    initialize_config(
        env="test",
        debug=True,
        agent={"model_type": "test-model"},
        memory={"embedding_size": 256},
        provider={"enabled_providers": ["local"]},
    )
