"""
PepperPy TTS Base Module.

Base interfaces and abstractions for text-to-speech functionality.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Protocol

from pepperpy.core.errors import PepperpyError


class TTSError(PepperpyError):
    """Base error for TTS operations."""

    pass


class TTSProviderError(TTSError):
    """Error raised by TTS providers."""

    pass


class TTSVoiceError(TTSProviderError):
    """Error related to voice operations."""

    pass


class TTSConfigError(TTSProviderError):
    """Error related to configuration."""

    pass


class TTSProvider(Protocol):
    """Protocol defining TTS provider interface."""

    async def convert_text(self, text: str, voice_id: str, **kwargs: Any) -> bytes:
        """Convert text to speech.

        Args:
            text: Text to convert
            voice_id: Voice identifier
            **kwargs: Additional provider-specific options

        Returns:
            Audio data as bytes
        """
        ...

    async def convert_text_stream(
        self, text: str, voice_id: str, **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """Stream audio from text.

        Args:
            text: Text to convert
            voice_id: Voice identifier
            **kwargs: Additional provider-specific options

        Returns:
            Async iterator of audio chunks
        """
        ...

    async def get_voices(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get available voices.

        Args:
            **kwargs: Provider-specific options

        Returns:
            List of voice information dictionaries
        """
        ...


class BaseTTSProvider(ABC):
    """Base implementation for TTS providers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize base TTS provider.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the TTS provider.

        Implementations should set self.initialized to True when complete.
        """
        self.initialized = True

    @abstractmethod
    async def convert_text(self, text: str, voice_id: str, **kwargs: Any) -> bytes:
        """Convert text to speech.

        Args:
            text: Text to convert
            voice_id: Voice identifier
            **kwargs: Additional provider-specific options

        Returns:
            Audio data as bytes
        """
        if not self.initialized:
            await self.initialize()
        raise TTSProviderError("Text conversion not implemented")

    @abstractmethod
    async def convert_text_stream(
        self, text: str, voice_id: str, **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """Stream audio from text.

        Args:
            text: Text to convert
            voice_id: Voice identifier
            **kwargs: Additional provider-specific options

        Returns:
            Async iterator of audio chunks
        """
        if not self.initialized:
            await self.initialize()

        # Default implementation for providers that don't support streaming
        # Just convert the whole text and yield it as a single chunk
        audio = await self.convert_text(text, voice_id, **kwargs)
        yield audio

    @abstractmethod
    async def get_voices(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get available voices.

        Args:
            **kwargs: Provider-specific options

        Returns:
            List of voice information dictionaries
        """
        if not self.initialized:
            await self.initialize()
        return []
