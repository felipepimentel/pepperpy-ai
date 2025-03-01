"""Public Interface for providers
This module provides a stable public interface for the providers functionality.
It exposes the core provider abstractions and implementations that are
considered part of the public API.

Provider Categories:
    LLM: Language model providers
    Embedding: Vector embedding providers
    Storage: Data storage providers
    Vision: Computer vision providers
    Audio: Audio processing providers
    Cloud: Cloud service providers
    Config: Configuration providers
"""

# Import public classes and functions from the implementation
from pepperpy.providers.agent.base import BaseProvider
from pepperpy.providers.agent.factory import ProviderFactory
from pepperpy.providers.agent.manager import ProviderManager

# Audio providers
from pepperpy.providers.audio.synthesis import SynthesisProvider
from pepperpy.providers.audio.transcription import TranscriptionProvider

# Cloud providers
from pepperpy.providers.cloud.aws import AWSProvider
from pepperpy.providers.cloud.gcp import GCPProvider

# Config providers
from pepperpy.providers.config.base import ConfigProvider
from pepperpy.providers.config.env import EnvConfigProvider
from pepperpy.providers.config.file import FileConfigProvider
from pepperpy.providers.config.filesystem import FilesystemConfigProvider
from pepperpy.providers.config.secure import SecureConfigProvider

# LLM providers
from pepperpy.providers.llm.anthropic import AnthropicProvider
from pepperpy.providers.llm.openai import OpenAIProvider
from pepperpy.providers.llm.openrouter import OpenRouterProvider
from pepperpy.providers.llm.perplexity import PerplexityProvider

# Storage providers
from pepperpy.providers.storage.cloud import CloudStorageProvider
from pepperpy.providers.storage.local import LocalStorageProvider
from pepperpy.providers.storage.sql import SQLStorageProvider

# Vision providers
from pepperpy.providers.vision.base import VisionProvider
from pepperpy.providers.vision.google import GoogleVisionProvider
from pepperpy.providers.vision.openai import OpenAIVisionProvider

__all__ = [
    # Base provider classes
    "BaseProvider",
    "ProviderFactory",
    "ProviderManager",
    # Audio providers
    "SynthesisProvider",
    "TranscriptionProvider",
    # Cloud providers
    "AWSProvider",
    "GCPProvider",
    "CloudStorageProvider",
    # Config providers
    "ConfigProvider",
    "EnvConfigProvider",
    "FileConfigProvider",
    "FilesystemConfigProvider",
    "SecureConfigProvider",
    # LLM providers
    "AnthropicProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "PerplexityProvider",
    # Storage providers
    "LocalStorageProvider",
    "SQLStorageProvider",
    # Vision providers
    "VisionProvider",
    "GoogleVisionProvider",
    "OpenAIVisionProvider",
]
