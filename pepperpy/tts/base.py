"""Base interfaces and types for TTS capabilities.

This module defines the core interfaces, data types, and factory for working with
Text-to-Speech providers in PepperPy.

Example:
    >>> from pepperpy.tts import TTSProvider, TTSFactory
    >>> provider = TTSFactory.create_provider("murf", api_key="...")
    >>> audio = await provider.convert_text("Hello world", voice_id="en-US-1")
"""

import os
from abc import abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Type

from pepperpy.core import PepperpyError
from pepperpy.core.base import BaseProvider


class TTSError(PepperpyError):
    """Base class for TTS errors."""


class TTSProviderError(TTSError):
    """Error raised by TTS providers during initialization or execution."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(message, *args, **kwargs)
        self.provider = provider
        self.operation = operation


class TTSConfigError(TTSError):
    """Error raised when TTS configuration is invalid."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        *args,
        **kwargs,
    ):
        super().__init__(message, *args, **kwargs)
        self.config_key = config_key
        self.config_value = config_value


class TTSVoiceError(TTSError):
    """Error raised when voice configuration or selection fails."""

    def __init__(
        self,
        message: str,
        voice_id: Optional[str] = None,
        voice_config: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(message, *args, **kwargs)
        self.voice_id = voice_id
        self.voice_config = voice_config or {}


class TTSCapabilities(str, Enum):
    """Capabilities that TTS providers may support."""

    TEXT_TO_SPEECH = "text_to_speech"
    STREAMING = "streaming"
    VOICE_CLONING = "voice_cloning"
    MULTILINGUAL = "multilingual"
    EMOTION_CONTROL = "emotion_control"


class TTSProvider(BaseProvider):
    """Provider interface for text-to-speech services."""

    async def initialize(self) -> None:
        """Initialize the provider."""
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        await super().cleanup()

    @abstractmethod
    async def convert_text(self, text: str, voice_id: str, **kwargs: Any) -> bytes:
        """Convert text to speech.

        Args:
            text: The text to convert to speech.
            voice_id: The ID of the voice to use.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Audio bytes.

        Raises:
            TTSError: If conversion fails.
        """
        ...

    @abstractmethod
    async def convert_text_stream(
        self, text: str, voice_id: str, **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """Stream generated audio from text.

        Args:
            text: The text to convert to speech.
            voice_id: The ID of the voice to use.
            **kwargs: Additional provider-specific parameters.

        Returns:
            An async iterator of audio chunks.

        Raises:
            TTSError: If streaming fails.
        """
        ...

    @abstractmethod
    async def get_voices(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get available voices.

        Args:
            **kwargs: Additional provider-specific parameters.

        Returns:
            List of voice information dictionaries.

        Raises:
            TTSError: If retrieving voices fails.
        """
        ...

    @abstractmethod
    async def clone_voice(self, name: str, samples: List[bytes], **kwargs: Any) -> str:
        """Clone a voice from audio samples.

        Args:
            name: Name for the cloned voice.
            samples: List of audio samples as bytes.
            **kwargs: Additional provider-specific parameters.

        Returns:
            ID of the created voice.

        Raises:
            TTSError: If voice cloning fails.
        """
        ...


class TTSFactory:
    """Factory for TTS provider instances."""

    # Map of provider types to their classes
    _PROVIDERS: Dict[str, Type[Any]] = {}

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[Any]) -> None:
        """Register a new provider type.

        Args:
            name: Name of the provider.
            provider_class: Provider class to register.
        """
        cls._PROVIDERS[name.lower()] = provider_class

    @classmethod
    def create_provider(
        cls, provider_type: Optional[str] = None, **kwargs: Any
    ) -> TTSProvider:
        """Create a TTS provider instance.

        Args:
            provider_type: Type of provider to create. If None, uses environment configuration.
            **kwargs: Additional configuration options passed to the provider.

        Returns:
            Configured TTS provider instance.

        Raises:
            TTSConfigError: If provider type is invalid or configuration is missing.
        """
        # If no provider type specified, get from environment
        if provider_type is None:
            provider_type = cls.get_default_provider()

        # Convert to lowercase for case-insensitive matching
        provider_type = provider_type.lower()

        # Check if provider type exists
        if provider_type not in cls._PROVIDERS:
            available_providers = ", ".join(cls._PROVIDERS.keys())
            raise TTSConfigError(
                f"Invalid TTS provider '{provider_type}'. "
                f"Available providers: {available_providers}"
            )

        # Create and return provider instance
        try:
            return cls._PROVIDERS[provider_type](**kwargs)
        except Exception as e:
            raise TTSConfigError(
                f"Failed to initialize TTS provider '{provider_type}': {str(e)}"
            )

    @staticmethod
    def get_default_provider() -> str:
        """Get the default provider type from environment.

        Returns:
            Provider type string.

        Raises:
            TTSConfigError: If provider configuration is missing.
        """
        provider = os.environ.get("PEPPERPY_TTS__PROVIDER", "").lower()

        if not provider:
            raise TTSConfigError(
                "No TTS provider specified. "
                "Set PEPPERPY_TTS__PROVIDER environment variable."
            )

        return provider
