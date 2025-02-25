"""Tests for security features.

This module tests the security features including:
- Rate limiting
- Security headers
- Input validation
- Audit logging
"""

import asyncio
import json
import logging
import pytest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from pepperpy.core.errors import ValidationError
from pepperpy.monitoring.audit import AuditLogger
from pepperpy.security.rate_limiter import RateLimiter
from pepperpy.security.errors import RateLimitError, SecurityError


@pytest.fixture
async def rate_limiter():
    """Create a rate limiter instance."""
    limiter = RateLimiter(requests_per_minute=60, burst_size=10)
    yield limiter


@pytest.fixture
async def audit_logger(tmp_path):
    """Create an audit logger instance."""
    audit_log_dir = tmp_path / "audit"
    audit_log_dir.mkdir()
    audit_file = audit_log_dir / "audit.log"
    
    logger = AuditLogger()
    logger.logger.handlers = []  # Remove default handlers
    handler = logging.FileHandler(audit_file)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.logger.addHandler(handler)
    
    yield logger, audit_file


async def test_rate_limiter_basic(rate_limiter):
    """Test basic rate limiting functionality."""
    # Test successful requests
    for _ in range(10):
        assert await rate_limiter.check_rate("test_user") is True

    # Test burst limit
    for _ in range(11):
        result = await rate_limiter.check_rate("test_user")
    assert result is False


async def test_rate_limiter_window(rate_limiter):
    """Test rate limiting window functionality."""
    # Fill up the window
    for _ in range(60):
        assert await rate_limiter.check_rate("test_user") is True

    # Next request should fail
    assert await rate_limiter.check_rate("test_user") is False

    # Wait for window to reset
    await asyncio.sleep(60)

    # Should work again
    assert await rate_limiter.check_rate("test_user") is True


async def test_rate_limiter_multiple_users(rate_limiter):
    """Test rate limiting for multiple users."""
    # Test user 1
    for _ in range(10):
        assert await rate_limiter.check_rate("user1") is True

    # Test user 2 (should not be affected by user1's limit)
    for _ in range(10):
        assert await rate_limiter.check_rate("user2") is True


async def test_audit_logging(audit_logger):
    """Test audit logging functionality."""
    logger, log_file = audit_logger

    # Test basic logging
    event = {
        "event_type": "test.event",
        "user": "test_user",
        "action": "test_action",
    }
    await logger.log(event)

    # Read log file
    with open(log_file, "r") as f:
        log_content = f.read()

    # Verify log content
    assert "test.event" in log_content
    assert "test_user" in log_content
    assert "test_action" in log_content


async def test_audit_logging_levels(audit_logger):
    """Test audit logging with different levels."""
    logger, log_file = audit_logger

    # Test different log levels
    levels = [
        (logging.DEBUG, "debug_event"),
        (logging.INFO, "info_event"),
        (logging.WARNING, "warning_event"),
        (logging.ERROR, "error_event"),
    ]

    for level, event_type in levels:
        await logger.log(
            {"event_type": event_type},
            level=level,
        )

    # Read log file
    with open(log_file, "r") as f:
        log_content = f.read()

    # Verify all events are logged
    for _, event_type in levels:
        assert event_type in log_content


async def test_audit_logging_metadata(audit_logger):
    """Test audit logging with metadata."""
    logger, log_file = audit_logger

    # Test with metadata
    event = {
        "event_type": "test.metadata",
        "timestamp": datetime.utcnow().isoformat(),
        "details": {
            "ip": "127.0.0.1",
            "session_id": "test_session",
            "status": "success",
        },
    }
    await logger.log(event)

    # Read log file
    with open(log_file, "r") as f:
        log_content = f.read()

    # Verify metadata is logged
    assert "127.0.0.1" in log_content
    assert "test_session" in log_content
    assert "success" in log_content


def test_security_headers():
    """Test security headers configuration."""
    from pepperpy.security import SecurityHeaders

    headers = SecurityHeaders(
        hsts_enabled=True,
        xss_protection=True,
        content_security_policy={
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline'",
        },
    )

    # Test HSTS header
    assert headers.get_headers()["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"

    # Test XSS protection header
    assert headers.get_headers()["X-XSS-Protection"] == "1; mode=block"

    # Test CSP header
    assert "default-src 'self'" in headers.get_headers()["Content-Security-Policy"]
    assert "script-src 'self' 'unsafe-inline'" in headers.get_headers()["Content-Security-Policy"]


def test_input_validation():
    """Test input validation functionality."""
    from pepperpy.security import validate_input, sanitize_output

    # Test valid input
    valid_input = {
        "user_id": "test_user_123",
        "action": "read",
        "parameters": {"key": "value"},
    }
    assert validate_input(valid_input) == valid_input

    # Test invalid input
    invalid_input = {
        "user_id": "test user 123",  # Contains spaces
        "action": "read",
    }
    with pytest.raises(ValidationError):
        validate_input(invalid_input)

    # Test output sanitization
    sensitive_data = {
        "password": "secret123",
        "api_key": "abc123",
        "user": {
            "name": "Test User",
            "email": "test@example.com",
        },
    }
    sanitized = sanitize_output(sensitive_data)
    assert "password" not in sanitized
    assert "api_key" not in sanitized
    assert sanitized["user"]["name"] == "Test User"
    assert sanitized["user"]["email"] == "test@example.com" 