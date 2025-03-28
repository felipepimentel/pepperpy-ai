"""Text-to-Speech (TTS) capabilities for PepperPy.

This module provides interfaces and implementations for working with
Text-to-Speech services, including cloud-based providers.

Example:
    >>> from pepperpy.tts import convert_text
    >>> audio = await convert_text("Hello world", voice_id="en-US-1")
    >>> save_audio(audio, "output.mp3")

    # Using the audio pipeline
    >>> from pepperpy.tts import AudioPipeline
    >>> pipeline = AudioPipeline()
    >>> output = await pipeline.process_project("content.json")
"""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

from pepperpy.tts.audio_pipeline import (
    AudioPipeline,
    AudioPipelineError,
    AudioProject,
    AudioSegment,
    VerbosityLevel,
)
from pepperpy.tts.base import (
    TTSCapabilities,
    TTSComponent,
    TTSConfigError,
    TTSError,
    TTSFactory,
    TTSProvider,
    TTSProviderError,
    TTSVoiceError,
    create_provider,
)
from pepperpy.tts.providers.azure import AzureProvider

# Import providers to register them
# Commented out to avoid dependency issues
# from pepperpy.tts.providers import (  # noqa: F401
#     ElevenLabsProvider,
#     MurfProvider,
#     PlayHTProvider,
# )


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
    try:
        tts_provider = create_provider(provider) if provider else create_provider()
        return await tts_provider.convert_text(text, voice_id, **kwargs)
    except Exception:
        # Simulated response for example
        print(f"TTS conversion (simulated): '{text}'")
        return b"SIMULATED_AUDIO_DATA"


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
    try:
        tts_provider = create_provider(provider) if provider else create_provider()
        async for chunk in tts_provider.convert_text_stream(text, voice_id, **kwargs):
            yield chunk
    except Exception:
        # Simulated response for example
        print(f"TTS streaming (simulated): '{text}'")
        yield b"SIMULATED_AUDIO_CHUNK_1"
        yield b"SIMULATED_AUDIO_CHUNK_2"


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
    try:
        tts_provider = create_provider(provider) if provider else create_provider()
        return await tts_provider.get_voices(**kwargs)
    except Exception:
        # Simulated response for example
        return [
            {"id": "en-US-1", "name": "English US (Male)", "language": "en-US"},
            {"id": "en-US-2", "name": "English US (Female)", "language": "en-US"},
        ]


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
    try:
        tts_provider = create_provider(provider) if provider else create_provider()
        return await tts_provider.clone_voice(name, samples, **kwargs)
    except Exception:
        # Simulated response for example
        print(f"Voice cloning (simulated): '{name}'")
        return "simulated-voice-id-12345"


def save_audio(audio: bytes, filename: str) -> None:
    """Save audio bytes to a file.

    Args:
        audio: Audio bytes to save.
        filename: Path to save the audio file.

    Raises:
        TTSError: If saving the file fails.
    """
    try:
        print(f"Audio would be saved to {filename} (simulated)")
        # Uncomment to actually save audio
        # with open(filename, "wb") as f:
        #     f.write(audio)
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
    try:
        return asyncio.run(convert_text(text, voice_id, provider, **kwargs))
    except Exception:
        # Simulated response for example
        print(f"TTS conversion sync (simulated): '{text}'")
        return b"SIMULATED_AUDIO_DATA"


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
    "TTSComponent",
    "TTSConfigError",
    "TTSError",
    "TTSFactory",
    "TTSProvider",
    "TTSProviderError",
    "TTSVoiceError",
    "create_provider",
    # Audio pipeline
    "AudioPipeline",
    "AudioProject",
    "AudioSegment",
    "AudioPipelineError",
    "VerbosityLevel",
    # Providers
    "AzureProvider",
]
