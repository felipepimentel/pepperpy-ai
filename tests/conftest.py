"""Test configuration and shared fixtures."""

import asyncio
import logging
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Generator

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture

from pepperpy.core.config import PepperpyConfig
from pepperpy.memory.store_config import PostgresConfig

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(autouse=True)
def clean_environment() -> Generator[None, None, None]:
    """Clean environment variables before and after each test."""
    original_env = dict(os.environ)
    for key in list(os.environ.keys()):
        if key.startswith("PEPPERPY_"):
            del os.environ[key]
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_config() -> PepperpyConfig:
    """Create a test configuration."""
    return PepperpyConfig.model_validate(
        {
            "agent": {
                "model_type": "test-model",
                "temperature": 0.7,
                "max_tokens": 1000,
                "timeout": 30,
            },
            "memory": {
                "vector_store_type": "faiss",
                "embedding_size": 256,
                "cache_ttl": 3600,
            },
            "provider": {
                "provider_type": "test",
                "api_key": "test-key",
                "model": "test-model",
                "max_retries": 3,
                "timeout": 30,
            },
        }
    )


@pytest.fixture
def env_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary environment file."""
    env_path = tmp_path / ".env"
    env_path.write_text("PEPPERPY_ENV=test\nPEPPERPY_DEBUG=true")
    yield env_path


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for testing."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def caplog(caplog: LogCaptureFixture) -> LogCaptureFixture:
    """Configure log capture."""
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
async def postgres_store() -> AsyncGenerator[PostgresConfig, None]:
    """Create a PostgreSQL store for testing."""
    config = PostgresConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "pepperpy_test"),
    )
    yield config


@pytest.fixture
def test_data_dir() -> Path:
    """Return the test data directory path."""
    TEST_DATA_DIR.mkdir(exist_ok=True)
    return TEST_DATA_DIR


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for configuration files.

    Args:
        tmp_path: Pytest's temporary directory fixture

    Returns:
        Path to the temporary configuration directory
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    yield config_dir


@pytest.fixture
def test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up test environment variables.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
    """
    monkeypatch.setenv("PEPPER_HUB_ENV", "test")
    monkeypatch.setenv("PEPPER_HUB_DEBUG", "true")


@pytest.fixture
def example_agent_config(temp_config_dir: Path) -> Path:
    """Create an example agent configuration file.

    Args:
        temp_config_dir: Temporary directory for test files

    Returns:
        Path to the example agent configuration file
    """
    config_path = temp_config_dir / "test_agent.yml"
    config_path.write_text("""
name: Test Agent
description: A test agent for unit testing
provider: test
model: test-model
memory:
    type: in_memory
    capacity: 10
events:
    - type: test_event
      handler: test_handler
      priority: 1
prompts:
    test: test_prompt
parameters:
    temperature: 0.7
    max_tokens: 100
""")
    return config_path


@pytest.fixture
def example_prompt_config(temp_config_dir: Path) -> Path:
    """Create an example prompt configuration file.

    Args:
        temp_config_dir: Temporary directory for test files

    Returns:
        Path to the example prompt configuration file
    """
    config_path = temp_config_dir / "test_prompt.yml"
    config_path.write_text("""
name: Test Prompt
description: A test prompt for unit testing
template: |
    This is a test prompt with variables:
    Topic: {{ topic }}
    Parameters: {{ parameters }}
variables:
    topic:
        type: string
        description: The topic to process
    parameters:
        type: object
        description: Additional parameters
examples:
    - variables:
        topic: Test Topic
        parameters:
            key: value
      output: Example output
""")
    return config_path


@pytest.fixture
def example_workflow_config(temp_config_dir: Path) -> Path:
    """Create an example workflow configuration file.

    Args:
        temp_config_dir: Temporary directory for test files

    Returns:
        Path to the example workflow configuration file
    """
    config_path = temp_config_dir / "test_workflow.yml"
    config_path.write_text("""
name: Test Workflow
description: A test workflow for unit testing
steps:
    - name: step1
      description: First test step
      agent: test_agent
      prompt: test_prompt
      inputs:
        topic: inputs.topic
        parameters: inputs.parameters
      outputs:
        result: outputs.step1_result
    - name: step2
      description: Second test step
      agent: test_agent
      prompt: test_prompt
      inputs:
        topic: outputs.step1_result
        parameters: inputs.parameters
      outputs:
        result: outputs.final_result
inputs:
    topic:
        type: string
        description: Input topic
    parameters:
        type: object
        description: Input parameters
outputs:
    step1_result:
        type: string
        description: Intermediate result
    final_result:
        type: string
        description: Final workflow result
""")
    return config_path
