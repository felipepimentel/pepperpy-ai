"""Base interfaces and types for TTS capabilities.

This module defines the core interfaces, data types, and factory for working with
Text-to-Speech providers in PepperPy.

Example:
    >>> from pepperpy.tts import TTSProvider, TTSFactory
    >>> provider = TTSFactory.create_provider("murf", api_key="...")
    >>> audio = await provider.convert_text("Hello world", voice_id="en-US-1")
"""

import os
import importlib
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, Type, Union

from pepperpy.core import PepperpyError
from pepperpy.core.base import BaseProvider, ValidationError
from pepperpy.workflow.base import WorkflowComponent


@dataclass
class TTSVoice:
    """Voice metadata for TTS."""
    
    id: str
    name: str
    gender: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "language": self.language,
            "description": self.description,
            "tags": self.tags,
        }


@dataclass
class TTSAudio:
    """Audio data returned from TTS."""
    
    audio_data: bytes
    content_type: str
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None
    
    def save(self, path: str) -> None:
        """Save audio to file.
        
        Args:
            path: Path to save audio to
        """
        with open(path, "wb") as f:
            f.write(self.audio_data)


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
    """Base class for TTS providers."""

    def __init__(
        self,
        voice_id: Optional[str] = None,
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> None:
        """Initialize TTS provider.

        Args:
            voice_id: Default voice ID
            output_format: Output audio format
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.voice_id = voice_id
        self.output_format = output_format

    async def initialize(self) -> None:
        """Initialize the provider."""
        pass

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs: Any,
    ) -> TTSAudio:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize
            voice_id: Voice ID to use
            output_path: Optional path to save audio
            **kwargs: Additional synthesis options

        Returns:
            TTSAudio object
        """
        pass

    @abstractmethod
    async def get_available_voices(self) -> List[TTSVoice]:
        """Get available voices.

        Returns:
            List of TTSVoice objects
        """
        pass
        
    async def convert_text(self, text: str, voice_id: Optional[str] = None, **kwargs: Any) -> TTSAudio:
        """Convert text to speech (alias for synthesize).

        Args:
            text: Text to convert
            voice_id: Voice identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            TTSAudio object

        Raises:
            TTSError: If conversion fails
        """
        return await self.synthesize(text, voice_id=voice_id, **kwargs)

    async def convert_text_stream(
        self, text: str, voice_id: Optional[str] = None, **kwargs: Any
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
            NotImplementedError: If streaming not supported
        """
        raise NotImplementedError("Streaming not supported by this provider")

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

    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration.
        
        Returns:
            Provider configuration
        """
        return {
            "voice_id": self.voice_id,
            "output_format": self.output_format,
        }


def create_provider(
    provider_type: str = "mock",
    **config: Any
) -> TTSProvider:
    """Create a TTS provider from the given type.
    
    Args:
        provider_type: Type of TTS provider
        **config: Provider configuration
        
    Returns:
        Configured TTS provider
        
    Raises:
        ValidationError: If provider creation fails
    """
    try:
        # Import provider module
        module_name = f"pepperpy.tts.providers.{provider_type}"
        module = importlib.import_module(module_name)
        
        # Get provider class name with proper capitalization
        provider_class_name = f"{provider_type.title()}TTSProvider"
        
        # Get provider class
        provider_class = getattr(module, provider_class_name)
        
        # Create provider instance
        return provider_class(**config)
    except (ImportError, AttributeError) as e:
        raise ValidationError(f"Failed to create TTS provider '{provider_type}': {e}")


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
    """Component for Text-to-Speech (TTS) operations.

    This component handles text-to-speech conversion using a TTS provider.
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
            component_id=component_id, name=name, config=config, metadata=metadata
        )
        self.provider: TTSProvider = provider

    async def process(self, data: str) -> bytes:
        """Process input text and convert to speech.

        Args:
            data: Input text to convert

        Returns:
            Audio data as bytes

        Raises:
            ValidationError: If input type is invalid
        """
        # Perform TTS conversion
        from pepperpy.core.base import ValidationError

        if not isinstance(data, str):
            raise ValidationError(
                f"Invalid input type for TTS component: {type(data).__name__}. "
                "Expected str."
            )

        voice_id = self.config.get("voice_id", "default")
        return await self.provider.convert_text(data, voice_id=voice_id)
