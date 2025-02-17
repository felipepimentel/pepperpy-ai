"""Domain exceptions for the providers module."""


class ProviderError(Exception):
    """Base class for provider-related exceptions."""

    pass


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider is not found."""

    pass


class ProviderInitializationError(ProviderError):
    """Raised when a provider fails to initialize."""

    pass


class ProviderConfigurationError(ProviderError):
    """Raised when a provider is misconfigured."""

    pass
