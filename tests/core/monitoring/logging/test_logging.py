"""Tests for logging functionality."""

import json
from datetime import datetime
from io import StringIO

import pytest

from pepperpy.core.monitoring.logging import LoggerFactory, LogLevel, LogRecord


@pytest.mark.asyncio
async def test_logger_basic(logger_factory: LoggerFactory, output_stream: StringIO):
    """Test basic logger functionality."""
    logger = logger_factory.get_logger("test")
    logger.info("Test message")

    output = output_stream.getvalue()
    log_data = json.loads(output)

    assert log_data["level"] == "info"
    assert log_data["message"] == "Test message"
    assert log_data["module"] == "test"


@pytest.mark.asyncio
async def test_logger_levels(logger_factory: LoggerFactory, output_stream: StringIO):
    """Test different log levels."""
    logger = logger_factory.get_logger("test")

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
async def test_logger_context(logger_factory: LoggerFactory, output_stream: StringIO):
    """Test logger context handling."""
    # Create logger with context
    logger = logger_factory.get_logger(
        "test",
        context={"app": "test_app"},
        metadata={"version": "1.0"},
    )

    logger.info("Test message")

    log_data = json.loads(output_stream.getvalue())
    assert log_data["context"]["app"] == "test_app"
    assert log_data["metadata"]["version"] == "1.0"


@pytest.mark.asyncio
async def test_logger_error_handling(
    logger_factory: LoggerFactory, output_stream: StringIO
):
    """Test error logging."""
    logger = logger_factory.get_logger("test")

    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Error occurred", error=e)

    log_data = json.loads(output_stream.getvalue())
    assert log_data["level"] == "error"
    assert log_data["error"]["type"] == "ValueError"
    assert log_data["error"]["message"] == "Test error"


@pytest.mark.asyncio
async def test_log_record():
    """Test log record creation and formatting."""
    # Create a log record
    record = LogRecord(
        level=LogLevel.INFO,
        message="Test message",
        module="test",
        context={"app": "test_app"},
        metadata={"version": "1.0"},
    )

    # Convert to dict
    data = record.to_dict()

    # Verify fields
    assert data["level"] == "info"
    assert data["message"] == "Test message"
    assert data["module"] == "test"
    assert data["context"]["app"] == "test_app"
    assert data["metadata"]["version"] == "1.0"
    assert datetime.fromisoformat(data["timestamp"])  # Valid timestamp


@pytest.mark.asyncio
async def test_logger_factory_cleanup(logger_factory: LoggerFactory):
    """Test logger factory cleanup."""
    # Create some loggers
    logger1 = logger_factory.get_logger("test1")
    logger2 = logger_factory.get_logger("test2")

    # Verify loggers are created
    assert logger_factory.get_logger("test1") is logger1
    assert logger_factory.get_logger("test2") is logger2

    # Clean up
    await logger_factory.cleanup()

    # Create new loggers
    new_logger1 = logger_factory.get_logger("test1")
    new_logger2 = logger_factory.get_logger("test2")

    # Verify they are different instances
    assert new_logger1 is not logger1
    assert new_logger2 is not logger2
