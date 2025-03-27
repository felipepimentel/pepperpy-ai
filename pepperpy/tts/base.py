"""Base interfaces and types for TTS capabilities.

This module defines the core interfaces, data types, and factory for working with
Text-to-Speech providers in PepperPy.

Example:
    >>> from pepperpy.tts import TTSProvider, TTSFactory
    >>> provider = TTSFactory.create_provider("murf", api_key="...")
    >>> audio = await provider.convert_text("Hello world", voice_id="en-US-1")
"""

import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Type

from pepperpy.core import PepperpyError
from pepperpy.core.base import BaseProvider
from pepperpy.core.workflow import ValidationError, WorkflowComponent


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


class TTSProvider(BaseProvider, ABC):
    """Base class for TTS providers."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize TTS provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional configuration options
        """
        super().__init__(name=name, config=config, **kwargs)

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str,
        output_format: str,
        **kwargs: Any,
    ) -> bytes:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize
            voice: Voice name to use
            output_format: Output audio format
            **kwargs: Additional synthesis options

        Returns:
            Audio data as bytes
        """
        pass

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
            text: Text to convert
            voice_id: Voice identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            Audio data as bytes

        Raises:
            TTSError: If conversion fails
        """
        pass

    @abstractmethod
    async def convert_text_stream(
        self, text: str, voice_id: str, **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """Stream audio from text.

        Args:
            text: Text to convert
            voice_id: Voice identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            AsyncIterator yielding audio chunks

        Raises:
            TTSError: If conversion fails
        """
        pass

    @abstractmethod
    async def get_voices(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Get available voices.

        Args:
            **kwargs: Provider-specific parameters

        Returns:
            List of voice information dictionaries

        Raises:
            TTSError: If retrieving voices fails
        """
        pass

    async def clone_voice(self, name: str, samples: List[bytes], **kwargs: Any) -> str:
        """Clone a voice from audio samples.

        Args:
            name: Name for the cloned voice
            samples: List of audio samples
            **kwargs: Provider-specific parameters

        Returns:
            ID of created voice

        Raises:
            TTSError: If voice cloning fails
            NotImplementedError: If provider doesn't support voice cloning
        """
        raise NotImplementedError("Voice cloning not supported by this provider")


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


class TTSComponent(WorkflowComponent):
    """Component for Text-to-Speech synthesis.

    This component handles the conversion of text to speech using a TTS provider.
    """

    def __init__(
        self,
        component_id: str,
        name: str,
        provider: TTSProvider,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize TTS component.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name
            provider: TTS provider implementation
            config: Optional configuration
            metadata: Optional metadata
        """
        super().__init__(
            component_id=component_id,
            name=name,
            provider=provider,
            config=config,
            metadata=metadata,
        )

    async def process(self, data: str) -> bytes:
        """Process input text and convert to speech.

        Args:
            data: Input text to convert

        Returns:
            Audio data as bytes

        Raises:
            ValidationError: If input type is invalid
        """
        if not isinstance(data, str):
            raise ValidationError(
                f"Invalid input type for TTS component: {type(data).__name__}. "
                "Expected str."
            )

        voice_id = self.config.get("voice_id")
        if not voice_id:
            raise ValidationError("voice_id not specified in component config")

        return await self.provider.convert_text(data, voice_id)
