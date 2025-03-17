"""HTTP module.

This module provides functionality for HTTP client and server.
"""

# Connection pooling
from pepperpy.http.client import HTTPConnectionPool

__all__ = [
    # Connection pooling
    "HTTPConnectionPool",
]
