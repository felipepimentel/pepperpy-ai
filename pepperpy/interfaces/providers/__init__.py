"""
Public Interface for providers

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
# Comentando importações que não existem
# from pepperpy.providers.cloud import (
#     AWSProvider,
#     GCPProvider,
# )
# Comentando importações que não existem
# from pepperpy.providers.config import (
#     ConfigProvider,
#     EnvConfigProvider,
#     FileConfigProvider,
#     SecureConfigProvider,
# )
# Atualizando importações para os novos caminhos
from pepperpy.providers.llm import (
    AnthropicProvider,
    OpenAIProvider,
    OpenRouterProvider,
    PerplexityProvider,
)
from pepperpy.providers.agent.base import BaseProvider

# Comentando importações que não existem
# from pepperpy.providers.agent.client import ProviderConfig
from pepperpy.providers.agent.factory import ProviderFactory
from pepperpy.providers.agent.manager import ProviderManager

# Atualizando importações para os novos caminhos
from pepperpy.providers.audio.synthesis import SynthesisProvider
from pepperpy.providers.audio.transcription import TranscriptionProvider

# Atualizando importações para os novos caminhos
from pepperpy.providers.vision import (
    GoogleVisionProvider,
    OpenAIVisionProvider,
    VisionProvider,
)

__all__ = [
    # Base
    "BaseProvider",
    # "ProviderConfig",  # Comentando classe que não existe
    "ProviderManager",
    "ProviderFactory",
    # LLM
    "OpenAIProvider",
    "AnthropicProvider",
    "PerplexityProvider",
    "OpenRouterProvider",
    # Vision
    "VisionProvider",
    "GoogleVisionProvider",
    "OpenAIVisionProvider",
    # Audio
    "TranscriptionProvider",
    "SynthesisProvider",
    # Comentando classes que não existem
    # # Cloud
    # "AWSProvider",
    # "GCPProvider",
    # # Config
    # "ConfigProvider",
    # "EnvConfigProvider",
    # "FileConfigProvider",
    # "SecureConfigProvider",
]
