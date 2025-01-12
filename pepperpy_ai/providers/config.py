"""Provider configuration module."""

from typing import TypedDict


class ProviderSettings(TypedDict, total=False):
    """Provider settings dictionary.

    Attributes:
        api_key: API key for authentication
        api_base: Base URL for API requests
        api_version: API version to use
        organization_id: Organization ID for multi-tenant providers
        model: Default model to use
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
    """

    api_key: str
    api_base: str
    api_version: str
    organization_id: str
    model: str
    timeout: float
    max_retries: int
    retry_delay: float


class ProviderConfig:
    """Provider configuration class.

    Attributes:
        api_key: The API key for the provider
        api_base: The base URL for API requests
        api_version: The API version to use
        organization_id: The organization ID for multi-tenant providers
        model: The default model to use
        timeout: The request timeout in seconds
        max_retries: The maximum number of retries
        retry_delay: The delay between retries in seconds
    """

    def __init__(
        self,
        api_key: str = "",
        api_base: str = "",
        api_version: str = "",
        organization_id: str = "",
        model: str = "",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize provider configuration.

        Args:
            api_key: The API key for the provider
            api_base: The base URL for API requests
            api_version: The API version to use
            organization_id: The organization ID for multi-tenant providers
            model: The default model to use
            timeout: The request timeout in seconds
            max_retries: The maximum number of retries
            retry_delay: The delay between retries in seconds
        """
        self.api_key = api_key
        self.api_base = api_base
        self.api_version = api_version
        self.organization_id = organization_id
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def to_dict(self) -> ProviderSettings:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return {
            "api_key": self.api_key,
            "api_base": self.api_base,
            "api_version": self.api_version,
            "organization_id": self.organization_id,
            "model": self.model,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
        }

    @classmethod
    def from_dict(cls, data: ProviderSettings) -> "ProviderConfig":
        """Create configuration from dictionary.

        Args:
            data: Dictionary containing configuration values

        Returns:
            Provider configuration instance
        """
        return cls(
            api_key=data.get("api_key", ""),
            api_base=data.get("api_base", ""),
            api_version=data.get("api_version", ""),
            organization_id=data.get("organization_id", ""),
            model=data.get("model", ""),
            timeout=data.get("timeout", 30.0),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 1.0),
        )
