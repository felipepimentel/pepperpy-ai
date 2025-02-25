"""Integration tests for security components.

This module tests the integration between different security components:
- Rate limiting with audit logging
- Security headers with input validation
- End-to-end request flow
"""

import logging
from typing import Any

import pytest

from pepperpy.core.errors import ValidationError
from pepperpy.monitoring.audit import AuditLogger
from pepperpy.security import (
    RateLimiter,
    SecurityHeaders,
    sanitize_output,
    validate_input,
)


class MockRequest:
    """Mock HTTP request for testing."""

    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
    ):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.data = data or {}


class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self):
        self.headers: dict[str, str] = {}
        self.status_code: int = 200
        self.data: dict[str, Any] = {}


@pytest.fixture
async def security_components(tmp_path):
    """Create security components for testing."""
    # Create audit logger
    audit_log_dir = tmp_path / "audit"
    audit_log_dir.mkdir()
    audit_file = audit_log_dir / "audit.log"

    logger = AuditLogger()
    logger.logger.handlers = []
    handler = logging.FileHandler(audit_file)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.logger.addHandler(handler)

    # Create rate limiter
    rate_limiter = RateLimiter(requests_per_minute=60, burst_size=10)

    # Create security headers
    security_headers = SecurityHeaders(
        hsts_enabled=True,
        xss_protection=True,
        content_security_policy={
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline'",
        },
    )

    return {
        "audit_logger": logger,
        "audit_file": audit_file,
        "rate_limiter": rate_limiter,
        "security_headers": security_headers,
    }


async def test_secure_request_flow(security_components):
    """Test complete secure request flow."""
    # Create mock request
    request = MockRequest(
        method="POST",
        path="/api/data",
        headers={
            "X-Request-ID": "test-123",
            "Authorization": "Bearer test-token",
        },
        data={
            "user_id": "test_user_123",
            "action": "read",
            "parameters": {"key": "value"},
        },
    )

    # Create mock response
    response = MockResponse()

    try:
        # 1. Check rate limit
        assert await security_components["rate_limiter"].check_rate(
            request.headers.get("X-Request-ID", "anonymous")
        )

        # 2. Validate input
        validated_data = validate_input(request.data)
        assert validated_data["user_id"] == "test_user_123"

        # 3. Process request (mock)
        response.data = {
            "status": "success",
            "data": validated_data,
            "sensitive": "secret123",
        }

        # 4. Sanitize output
        response.data = sanitize_output(response.data)
        assert "sensitive" not in response.data

        # 5. Add security headers
        response.headers = security_components["security_headers"].get_headers()
        assert "Strict-Transport-Security" in response.headers

        # 6. Log audit event
        await security_components["audit_logger"].log({
            "event_type": "api.request",
            "method": request.method,
            "path": request.path,
            "user_id": validated_data["user_id"],
            "status": "success",
        })

        # Verify audit log
        with open(security_components["audit_file"]) as f:
            log_content = f.read()
            assert "api.request" in log_content
            assert "test_user_123" in log_content
            assert "success" in log_content

    except Exception as e:
        # Log error and re-raise
        await security_components["audit_logger"].log({
            "event_type": "api.error",
            "error": str(e),
            "request_id": request.headers.get("X-Request-ID"),
        })
        raise


async def test_rate_limit_with_audit(security_components):
    """Test rate limiting with audit logging."""
    request_id = "test-456"

    # Fill up rate limit
    for _ in range(60):
        assert await security_components["rate_limiter"].check_rate(request_id)

    # Next request should fail
    assert not await security_components["rate_limiter"].check_rate(request_id)

    # Verify audit log contains rate limit event
    with open(security_components["audit_file"]) as f:
        log_content = f.read()
        assert "rate_limit" in log_content
        assert request_id in log_content


async def test_invalid_input_handling(security_components):
    """Test handling of invalid input."""
    invalid_data = {
        "user_id": "test user 123",  # Contains spaces
        "action": "read",
    }

    try:
        validate_input(invalid_data)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        # Verify audit log contains validation error
        await security_components["audit_logger"].log({
            "event_type": "validation.error",
            "data": invalid_data,
        })

        with open(security_components["audit_file"]) as f:
            log_content = f.read()
            assert "validation.error" in log_content


async def test_security_headers_all_features(security_components):
    """Test all security header features."""
    headers = security_components["security_headers"]

    # Test with all features enabled
    all_headers = headers.get_headers()
    assert "Strict-Transport-Security" in all_headers
    assert "X-XSS-Protection" in all_headers
    assert "Content-Security-Policy" in all_headers
    assert "X-Frame-Options" in all_headers
    assert "X-Content-Type-Options" in all_headers
    assert "Referrer-Policy" in all_headers

    # Test with features disabled
    headers = SecurityHeaders(
        hsts_enabled=False,
        xss_protection=False,
    )
    disabled_headers = headers.get_headers()
    assert "Strict-Transport-Security" not in disabled_headers
    assert "X-XSS-Protection" not in disabled_headers
