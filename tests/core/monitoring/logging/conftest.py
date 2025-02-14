"""Test fixtures for logging tests."""

from io import StringIO
from typing import AsyncGenerator, Generator

import pytest

from pepperpy.core.monitoring.logging import LoggerFactory


@pytest.fixture
def output_stream() -> Generator[StringIO, None, None]:
    """Create a string buffer for capturing log output."""
    stream = StringIO()
    yield stream
    stream.close()


@pytest.fixture
async def logger_factory(
    output_stream: StringIO,
) -> AsyncGenerator[LoggerFactory, None]:
    """Create a logger factory for testing."""
    factory = LoggerFactory(output=output_stream)
    yield factory
    await factory.cleanup()
