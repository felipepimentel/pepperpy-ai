"""Provider configuration module."""

from .base import BaseConfig


class ProviderConfig(BaseConfig):
    """Configuration for providers.

    This class provides configuration options for providers, including API
    settings, model parameters, and other options that control provider
    behavior.
    """

    def __init__(
        self,
        name: str,
        version: str,
        api_key: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        organization_id: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enabled: bool = True,
    ) -> None:
        """Initialize provider configuration.

        Args:
            name: Provider name.
            version: Provider version.
            api_key: API key for authentication.
            api_base: Base URL for API requests.
            api_version: API version to use.
            organization_id: Organization ID for API requests.
            model: Default model to use.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries.
            retry_delay: Delay between retries in seconds.
            enabled: Whether provider is enabled.
        """
        super().__init__(name=name, version=version, enabled=enabled)
        self.api_key = api_key
        self.api_base = api_base
        self.api_version = api_version
        self.organization_id = organization_id
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
