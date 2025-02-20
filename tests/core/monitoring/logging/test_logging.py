"""Tests for logging functionality."""

import json
import logging
from io import StringIO

import pytest

from pepperpy.monitoring import configure_logging


@pytest.mark.asyncio
async def test_logger_basic(output_stream: StringIO):
    """Test basic logger functionality."""
    configure_logging()
    logger = logging.getLogger("test")
    logger.info("Test message")

    output = output_stream.getvalue()
    log_data = json.loads(output)

    assert log_data["level"] == "info"
    assert log_data["message"] == "Test message"
    assert log_data["module"] == "test"


@pytest.mark.asyncio
async def test_logger_levels(output_stream: StringIO):
    """Test different log levels."""
    configure_logging()
    logger = logging.getLogger("test")

    # Test all log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    # Parse output
    logs = [json.loads(line) for line in output_stream.getvalue().splitlines()]

    # Verify levels
    assert logs[0]["level"] == "debug"
    assert logs[1]["level"] == "info"
    assert logs[2]["level"] == "warning"
    assert logs[3]["level"] == "error"
    assert logs[4]["level"] == "critical"


@pytest.mark.asyncio
async def test_logger_context(output_stream: StringIO):
    """Test logger context handling."""
    configure_logging()
    logger = logging.getLogger("test")
    logger.info("Test message", extra={"app": "test_app", "version": "1.0"})

    log_data = json.loads(output_stream.getvalue())
    assert log_data["app"] == "test_app"
    assert log_data["version"] == "1.0"


@pytest.mark.asyncio
async def test_logger_error_handling(output_stream: StringIO):
    """Test error logging."""
    configure_logging()
    logger = logging.getLogger("test")

    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Error occurred", extra={"error": str(e)})

    log_data = json.loads(output_stream.getvalue())
    assert log_data["level"] == "error"
    assert log_data["error"] == "Test error"


@pytest.mark.asyncio
async def test_log_levels():
    """Test log level handling."""
    # Test level comparison
    assert logging.DEBUG < logging.INFO
    assert logging.INFO < logging.WARNING
    assert logging.WARNING < logging.ERROR
    assert logging.ERROR < logging.CRITICAL

    # Test string conversion
    assert logging.getLevelName(logging.INFO).lower() == "info"
    assert logging.getLevelName(logging.ERROR).lower() == "error"


@pytest.fixture
def output_stream() -> StringIO:
    """Provide a string buffer for capturing log output."""
    return StringIO()
