"""Security middleware for the AI Gateway."""

import ipaddress
import re
import time
from collections.abc import Callable
from typing import Any

import jwt
from fastapi import Request, Response
from prometheus_client import Counter, Histogram

# Metrics
auth_failures = Counter(
    "ai_gateway_auth_failures_total", "Total authentication failures", ["reason"]
)

rate_limits = Counter(
    "ai_gateway_rate_limit_exceeded_total", "Total rate limit violations", ["endpoint"]
)

request_duration = Histogram(
    "ai_gateway_request_duration_seconds", "Request duration in seconds", ["endpoint"]
)


class SecurityMiddleware:
    """Security middleware for request validation and protection."""

    def __init__(
        self,
        jwt_secret: str,
        rate_limits: dict[str, int],
        allowed_ips: list[str] | None = None,
        blocked_ips: list[str] | None = None,
    ):
        """Initialize security middleware.

        Args:
            jwt_secret: Secret for JWT validation
            rate_limits: Requests per minute by endpoint
            allowed_ips: Allowed IP ranges (optional)
            blocked_ips: Blocked IP ranges (optional)
        """
        self.jwt_secret = jwt_secret
        self.rate_limits = rate_limits
        self.request_counts: dict[str, dict[str, int]] = {}
        self.last_cleanup = time.time()

        # Convert IP ranges to network objects
        self.allowed_networks = [ipaddress.ip_network(ip) for ip in (allowed_ips or [])]
        self.blocked_networks = [ipaddress.ip_network(ip) for ip in (blocked_ips or [])]

        # Regex for input validation
        self.safe_pattern = re.compile(r"^[\w\s\-.,?!]+$")

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from next handler
        """
        start_time = time.time()

        try:
            # IP validation
            client_ip = ipaddress.ip_address(request.client.host)

            if self.blocked_networks and any(
                client_ip in net for net in self.blocked_networks
            ):
                auth_failures.labels(reason="blocked_ip").inc()
                return Response(content="IP blocked", status_code=403)

            if self.allowed_networks and not any(
                client_ip in net for net in self.allowed_networks
            ):
                auth_failures.labels(reason="ip_not_allowed").inc()
                return Response(content="IP not allowed", status_code=403)

            # JWT validation
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                request.state.user = payload
            except jwt.InvalidTokenError:
                auth_failures.labels(reason="invalid_token").inc()
                return Response(content="Invalid token", status_code=401)

            # Rate limiting
            endpoint = request.url.path
            user_id = payload.get("sub", "anonymous")

            if not self._check_rate_limit(endpoint, user_id):
                rate_limits.labels(endpoint=endpoint).inc()
                return Response(content="Rate limit exceeded", status_code=429)

            # Input validation for text endpoints
            if request.method == "POST" and "text" in (await request.json()):
                text = (await request.json())["text"]
                if not self._validate_input(text):
                    auth_failures.labels(reason="invalid_input").inc()
                    return Response(content="Invalid input", status_code=400)

            # Process request
            response = await call_next(request)

            # Record metrics
            request_duration.labels(endpoint=endpoint).observe(time.time() - start_time)

            return response

        except Exception:
            auth_failures.labels(reason="middleware_error").inc()
            return Response(content="Security error", status_code=500)

    def _check_rate_limit(self, endpoint: str, user_id: str) -> bool:
        """Check if request is within rate limits.

        Args:
            endpoint: API endpoint
            user_id: User identifier

        Returns:
            Whether request is allowed
        """
        now = time.time()

        # Cleanup old entries every minute
        if now - self.last_cleanup > 60:
            self._cleanup_old_requests()
            self.last_cleanup = now

        # Get rate limit for endpoint
        limit = self.rate_limits.get(endpoint, 60)  # Default 60 rpm

        # Initialize counters
        if endpoint not in self.request_counts:
            self.request_counts[endpoint] = {}
        if user_id not in self.request_counts[endpoint]:
            self.request_counts[endpoint][user_id] = 0

        # Check and update count
        count = self.request_counts[endpoint][user_id]
        if count >= limit:
            return False

        self.request_counts[endpoint][user_id] += 1
        return True

    def _cleanup_old_requests(self) -> None:
        """Remove old request counts."""
        self.request_counts = {}

    def _validate_input(self, text: str) -> bool:
        """Validate input text.

        Args:
            text: Input text to validate

        Returns:
            Whether input is valid
        """
        return bool(self.safe_pattern.match(text))


class ContentFilter:
    """Content filtering for request/response validation."""

    def __init__(self):
        """Initialize content filter."""
        # Add your content filtering rules here
        pass

    def validate_request(self, content: dict[str, Any]) -> bool:
        """Validate request content.

        Args:
            content: Request content

        Returns:
            Whether content is valid
        """
        # Implement request validation
        return True

    def validate_response(self, content: dict[str, Any]) -> bool:
        """Validate response content.

        Args:
            content: Response content

        Returns:
            Whether content is valid
        """
        # Implement response validation
        return True
