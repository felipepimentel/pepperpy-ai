"""Client configuration module."""

from .base import BaseConfig


class ClientConfig(BaseConfig):
    """Configuration for clients.

    This class provides configuration options for clients, including API
    settings, connection parameters, and other options that control client
    behavior.
    """

    def __init__(
        self,
        name: str,
        version: str,
        enabled: bool = True,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_connections: int = 10,
        keep_alive: bool = True,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize client configuration.

        Args:
            name: Client name.
            version: Client version.
            enabled: Whether client is enabled.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries.
            retry_delay: Delay between retries in seconds.
            max_connections: Maximum concurrent connections.
            keep_alive: Whether to keep connections alive.
            verify_ssl: Whether to verify SSL certificates.
        """
        super().__init__(name=name, version=version, enabled=enabled)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_connections = max_connections
        self.keep_alive = keep_alive
        self.verify_ssl = verify_ssl
