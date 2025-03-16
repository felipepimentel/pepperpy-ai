"""Base classes for providers in PepperPy.

This module re-exports the core provider interfaces from pepperpy.core.providers.
All provider implementations should use these interfaces.

Example:
    ```python
    from pepperpy.providers.base import Provider

    class MyCustomProvider(Provider):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # Custom initialization

        def connect(self):
            # Custom connection logic
            pass
    ```
"""

from pepperpy.core.providers import (
    AsyncProvider,
    AuthenticationError,
    NetworkError,
    Provider,
    ProviderError,
    RateLimitError,
    RESTProvider,
    ServerError,
    StorageProvider,
    TimeoutError,
)

# Export all classes
__all__ = [
    # Base provider classes
    "Provider",
    "AsyncProvider",
    "RESTProvider",
    "StorageProvider",
    # Error classes
    "ProviderError",
    "AuthenticationError",
    "NetworkError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
]
