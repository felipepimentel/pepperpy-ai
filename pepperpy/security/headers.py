"""Security headers implementation.

This module provides security headers configuration and management
for HTTP responses.
"""

from typing import Dict, Optional

from pepperpy.core.errors import ValidationError
from pepperpy.monitoring import logger


class SecurityHeaders:
    """Security headers configuration."""

    def __init__(
        self,
        hsts_enabled: bool = True,
        xss_protection: bool = True,
        content_security_policy: Optional[Dict[str, str]] = None,
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        referrer_policy: str = "strict-origin-when-cross-origin",
    ) -> None:
        """Initialize security headers.

        Args:
            hsts_enabled: Whether to enable HSTS
            xss_protection: Whether to enable XSS protection
            content_security_policy: CSP configuration
            frame_options: X-Frame-Options value
            content_type_options: X-Content-Type-Options value
            referrer_policy: Referrer-Policy value
        """
        self.hsts_enabled = hsts_enabled
        self.xss_protection = xss_protection
        self.content_security_policy = content_security_policy or {
            "default-src": "'self'",
            "script-src": "'self'",
            "style-src": "'self'",
            "img-src": "'self'",
            "connect-src": "'self'",
            "font-src": "'self'",
            "object-src": "'none'",
            "media-src": "'self'",
            "frame-src": "'none'",
            "sandbox": "allow-forms allow-scripts",
            "report-uri": "/security/csp-report",
        }
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.referrer_policy = referrer_policy

        # Validate configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate security headers configuration."""
        # Validate frame options
        valid_frame_options = {"DENY", "SAMEORIGIN", "ALLOW-FROM"}
        if self.frame_options not in valid_frame_options:
            raise ValidationError(
                f"Invalid frame options: {self.frame_options}. "
                f"Must be one of: {valid_frame_options}"
            )

        # Validate content type options
        if self.content_type_options != "nosniff":
            raise ValidationError(
                f"Invalid content type options: {self.content_type_options}. "
                "Must be 'nosniff'"
            )

        # Validate referrer policy
        valid_referrer_policies = {
            "no-referrer",
            "no-referrer-when-downgrade",
            "origin",
            "origin-when-cross-origin",
            "same-origin",
            "strict-origin",
            "strict-origin-when-cross-origin",
            "unsafe-url",
        }
        if self.referrer_policy not in valid_referrer_policies:
            raise ValidationError(
                f"Invalid referrer policy: {self.referrer_policy}. "
                f"Must be one of: {valid_referrer_policies}"
            )

        # Log validation success
        logger.debug("Security headers configuration validated successfully")

    def get_headers(self) -> Dict[str, str]:
        """Get security headers.

        Returns:
            Dict[str, str]: Security headers
        """
        headers = {
            "X-Frame-Options": self.frame_options,
            "X-Content-Type-Options": self.content_type_options,
            "Referrer-Policy": self.referrer_policy,
        }

        # Add HSTS header
        if self.hsts_enabled:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Add XSS protection header
        if self.xss_protection:
            headers["X-XSS-Protection"] = "1; mode=block"

        # Add CSP header
        if self.content_security_policy:
            csp_value = "; ".join(
                f"{key} {value}"
                for key, value in self.content_security_policy.items()
            )
            headers["Content-Security-Policy"] = csp_value

        return headers

    def apply_headers(self, response: Dict[str, str]) -> Dict[str, str]:
        """Apply security headers to a response.

        Args:
            response: Response headers

        Returns:
            Dict[str, str]: Updated response headers
        """
        headers = self.get_headers()
        response.update(headers)
        return response 