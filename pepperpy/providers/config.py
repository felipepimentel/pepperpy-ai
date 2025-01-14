"""Provider configuration module."""

from dataclasses import dataclass

from pepperpy.types import BaseConfig


@dataclass
class BaseProviderConfig:
    """Base provider configuration.

    Attributes:
        name: Provider name.
        version: Provider version.
        provider: Provider type.
    """

    name: str
    version: str
    provider: str


@dataclass
class ProviderConfig(BaseConfig, BaseProviderConfig):
    """Provider configuration.

    Attributes:
        name: Provider name.
        version: Provider version.
        provider: Provider type.
        description: Optional provider description.
        settings: Optional provider-specific settings.
        metadata: Optional metadata about the provider.
    """

    description: str | None = None
