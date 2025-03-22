"""Text-to-Speech (TTS) capabilities for PepperPy.

This module provides interfaces and implementations for working with
Text-to-Speech services, including cloud-based providers.

Example:
    >>> from pepperpy.tts import convert_text
    >>> audio = await convert_text("Hello world", voice_id="en-US-1")
    >>> save_audio(audio, "output.mp3")
"""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

from pepperpy.tts.base import (
    TTSCapabilities,
    TTSConfigError,
    TTSError,
    TTSFactory,
    TTSProvider,
    TTSProviderError,
    TTSVoiceError,
)

# Import providers to register them
from pepperpy.tts.providers import (  # noqa: F401
    ElevenLabsProvider,
    MurfProvider,
    PlayHTProvider,
)


async def convert_text(
    text: str, voice_id: str, provider: Optional[str] = None, **kwargs
) -> bytes:
    """Convert text to speech.

    Args:
        text: The text to convert to speech.
        voice_id: The ID of the voice to use.
        provider: Optional provider to use. If None, uses environment configuration.
        **kwargs: Additional provider-specific parameters.

    Returns:
        Audio bytes.

    Raises:
        TTSError: If conversion fails.
    """
    tts_provider = TTSFactory.create_provider(provider)
    return await tts_provider.convert_text(text, voice_id, **kwargs)


async def convert_text_stream(
    text: str, voice_id: str, provider: Optional[str] = None, **kwargs
) -> AsyncIterator[bytes]:
    """Stream audio from text.

    Args:
        text: The text to convert to speech.
        voice_id: The ID of the voice to use.
        provider: Optional provider to use. If None, uses environment configuration.
        **kwargs: Additional provider-specific parameters.

    Returns:
        An async iterator of audio chunks.

    Raises:
        TTSError: If conversion fails.
    """
    tts_provider = TTSFactory.create_provider(provider)
    async for chunk in tts_provider.convert_text_stream(text, voice_id, **kwargs):
        yield chunk


async def get_voices(provider: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
    """Get available voices.

    Args:
        provider: Optional provider to use. If None, uses environment configuration.
        **kwargs: Additional provider-specific parameters.

    Returns:
        List of voice information dictionaries.

    Raises:
        TTSError: If retrieving voices fails.
    """
    tts_provider = TTSFactory.create_provider(provider)
    return await tts_provider.get_voices(**kwargs)


async def clone_voice(
    name: str, samples: List[bytes], provider: Optional[str] = None, **kwargs
) -> str:
    """Clone a voice from audio samples.

    Args:
        name: Name for the cloned voice.
        samples: List of audio samples as bytes.
        provider: Optional provider to use. If None, uses environment configuration.
        **kwargs: Additional provider-specific parameters.

    Returns:
        ID of the created voice.

    Raises:
        TTSError: If voice cloning fails.
    """
    tts_provider = TTSFactory.create_provider(provider)
    return await tts_provider.clone_voice(name, samples, **kwargs)


def save_audio(audio: bytes, filename: str) -> None:
    """Save audio bytes to a file.

    Args:
        audio: Audio bytes to save.
        filename: Path to save the audio file.

    Raises:
        TTSError: If saving the file fails.
    """
    try:
        with open(filename, "wb") as f:
            f.write(audio)
    except Exception as e:
        raise TTSError(f"Failed to save audio to {filename}: {str(e)}") from e


def convert_text_sync(
    text: str, voice_id: str, provider: Optional[str] = None, **kwargs
) -> bytes:
    """Synchronous version of convert_text.

    Args:
        text: The text to convert to speech.
        voice_id: The ID of the voice to use.
        provider: Optional provider to use. If None, uses environment configuration.
        **kwargs: Additional provider-specific parameters.

    Returns:
        Audio bytes.

    Raises:
        TTSError: If conversion fails.
    """
    return asyncio.run(convert_text(text, voice_id, provider, **kwargs))


__all__ = [
    # High-level API
    "convert_text",
    "convert_text_stream",
    "convert_text_sync",
    "get_voices",
    "clone_voice",
    "save_audio",
    # Base types and interfaces
    "TTSCapabilities",
    "TTSConfigError",
    "TTSError",
    "TTSFactory",
    "TTSProvider",
    "TTSProviderError",
    "TTSVoiceError",
]
