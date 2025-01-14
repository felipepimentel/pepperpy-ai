"""Capability configuration module."""

from typing import Any

from .base import BaseConfig


class CapabilityConfig(BaseConfig):
    """Configuration for capabilities.

    This class provides configuration options for capabilities, including
    model settings, resource limits, and other parameters that control
    capability behavior.
    """

    def __init__(
        self,
        name: str,
        version: str,
        model: str | None = None,
        enabled: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        batch_size: int = 32,
        api_key: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
        organization_id: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> None:
        """Initialize capability configuration.

        Args:
            name: Capability name.
            version: Capability version.
            model: Model name or path.
            enabled: Whether capability is enabled.
            max_retries: Maximum number of retries.
            retry_delay: Delay between retries in seconds.
            timeout: Operation timeout in seconds.
            batch_size: Batch size for operations.
            api_key: API key for authentication.
            api_base: Base URL for API requests.
            api_version: API version to use.
            organization_id: Organization ID for API requests.
            settings: Additional capability settings.
        """
        super().__init__(name=name, version=version)
        self.enabled = enabled
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.batch_size = batch_size
        self.api_key = api_key
        self.api_base = api_base
        self.api_version = api_version
        self.organization_id = organization_id
        self.settings = settings or {}
