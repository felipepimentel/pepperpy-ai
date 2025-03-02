"""Public Interface for providers

This module provides a stable public interface for provider abstractions.
It exposes the core provider interfaces that are considered part of the public API.

Provider Categories:
    LLM: Language model provider interfaces
    Embedding: Vector embedding provider interfaces
    Storage: Data storage provider interfaces
    Vision: Computer vision provider interfaces
    Audio: Audio processing provider interfaces
    Cloud: Cloud service provider interfaces
    Config: Configuration provider interfaces
"""

# Re-export provider interfaces
from pepperpy.interfaces.storage import StorageError, StorageProvider


# Define provider interface types
class ProviderInterface:
    """Base marker class for all provider interfaces."""

    pass


class LLMProviderInterface(ProviderInterface):
    """Interface for LLM providers."""

    pass


class EmbeddingProviderInterface(ProviderInterface):
    """Interface for embedding providers."""

    pass


class VisionProviderInterface(ProviderInterface):
    """Interface for vision providers."""

    pass


class AudioProviderInterface(ProviderInterface):
    """Interface for audio providers."""

    pass


class CloudProviderInterface(ProviderInterface):
    """Interface for cloud providers."""

    pass


class ConfigProviderInterface(ProviderInterface):
    """Interface for configuration providers."""

    pass


# Export the interfaces
__all__ = [
    # Base interfaces
    "ProviderInterface",
    "LLMProviderInterface",
    "EmbeddingProviderInterface",
    "VisionProviderInterface",
    "AudioProviderInterface",
    "CloudProviderInterface",
    "ConfigProviderInterface",
    # Storage interfaces
    "StorageError",
    "StorageProvider",
]
