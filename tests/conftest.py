"""Test configuration and fixtures."""

import asyncio
import logging
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from pepperpy.core.config import PepperpyConfig
from pepperpy.memory.store_config import PostgresConfig

# Configure logging
logging.basicConfig(level=logging.DEBUG)


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
