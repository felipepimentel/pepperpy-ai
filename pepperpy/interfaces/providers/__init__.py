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
from pepperpy.providers.cloud.storage import CloudStorageProvider

# Config providers
from pepperpy.providers.config.base import ConfigProvider
from pepperpy.providers.config.env import EnvConfigProvider
from pepperpy.providers.config.file import FileConfigProvider
from pepperpy.providers.config.filesystem import FilesystemConfigProvider
from pepperpy.providers.config.secure import SecureConfigProvider

# LLM providers
from pepperpy.providers.llm.anthropic import AnthropicProvider
from pepperpy.providers.llm.openai import OpenAIProvider
