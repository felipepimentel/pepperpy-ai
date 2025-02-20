"""Security module.

This module provides security functionality:
- Encryption and decryption
- Rate limiting
- Access control
- Input validation
- Audit logging
"""

from pepperpy.security.rate_limiter import RateLimiter

__all__ = ["RateLimiter"]
