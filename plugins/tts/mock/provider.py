"""
Mock TTS Provider.

Implements text-to-speech capabilities for testing without requiring API keys.
"""

import asyncio
import io
import math
import os
import struct
import wave
from collections.abc import AsyncIterator
from typing import Any, List, Optional

from pepperpy.tts.base import (
    TTSAudio,
    TTSCapabilities,
    TTSProvider,
    TTSVoice,
)


class MockTTSProvider(TTSProvider):
    """Mock TTS provider for testing and development."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the mock provider."""
        super().__init__(**kwargs)
        self.voice_id = kwargs.get("voice_id", "mock-male-en")
        self.output_format = kwargs.get("output_format", "wav")
        self._test_mode = (
            os.environ.get("PEPPERPY_DEV__MODE", "false").lower() == "true"
        )
        self._initialized = False
        print("DEBUG: Checking for env var PEPPERPY_TTS__MOCK_API_KEY")

    @classmethod
    def from_config(cls, **config: Any) -> "MockTTSProvider":
        """Create an instance from configuration."""
        instance = cls()

        # Voice ID
        if "voice_id" in config:
            instance.voice_id = config["voice_id"]

        # Output format
        if "output_format" in config:
            instance.output_format = config["output_format"]

        return instance

    @property
    def capabilities(self) -> List[TTSCapabilities]:
        """Return the capabilities of this provider."""
        return [
            TTSCapabilities.TEXT_TO_SPEECH,
            TTSCapabilities.STREAMING,
            TTSCapabilities.MULTILINGUAL,
        ]

    async def initialize(self) -> None:
        """Initialize the provider."""
        print("DEBUG: Initializing mock TTS provider in test mode.")
        self._initialized = True

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
        print(f"DEBUG: Mock TTS: Synthesizing text: '{text[:50]}...'")
        voice_id = voice_id or self.voice_id

        # Generate a simple sine wave as audio data
        audio_data = self._generate_test_audio(text)

        audio = TTSAudio(
            audio_data=audio_data,
            content_type="audio/wav",
            duration_seconds=1.0,
            sample_rate=16000,
        )

        if output_path:
            print(f"DEBUG: Mock TTS: Saving to {output_path}")
            audio.save(output_path)

        return audio

    def _generate_test_audio(self, text: str) -> bytes:
        """Generate a test audio sample."""
        # Generate a simple beep sound using wave
        freq = 440.0  # A4 note frequency
        duration = 1.0  # 1 second
        sample_rate = 16000  # 16kHz
        amplitude = 16000  # Max amplitude

        # Generate sine wave
        num_samples = int(duration * sample_rate)
        samples = []
        for i in range(num_samples):
            # Simple formula to vary frequency based on text length
            variation = (hash(text) % 200) / 100
            adjusted_freq = freq * (1 + variation)

            sample = amplitude * math.sin(2 * math.pi * adjusted_freq * i / sample_rate)
            samples.append(int(sample))

        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)

            # Pack all samples into bytes
            packed_samples = struct.pack(f"<{len(samples)}h", *samples)
            wav_file.writeframes(packed_samples)

        return buffer.getvalue()

    async def get_available_voices(self) -> List[TTSVoice]:
        """Get available voices.

        Returns:
            List of TTSVoice objects
        """
        # Return a list of mock voices
        return [
            TTSVoice(
                id="mock-male-en",
                name="Mock Male (English)",
                gender="male",
                language="en-US",
                description="A mock male voice for testing",
                tags=["test", "male", "english"],
            ),
            TTSVoice(
                id="mock-female-en",
                name="Mock Female (English)",
                gender="female",
                language="en-US",
                description="A mock female voice for testing",
                tags=["test", "female", "english"],
            ),
            TTSVoice(
                id="mock-male-es",
                name="Mock Male (Spanish)",
                gender="male",
                language="es-ES",
                description="A mock male Spanish voice for testing",
                tags=["test", "male", "spanish"],
            ),
        ]

    async def convert_text(
        self, text: str, voice_id: Optional[str] = None, **kwargs: Any
    ) -> bytes:
        """Convert text to speech (alias for synthesize).

        Args:
            text: Text to convert
            voice_id: Voice identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            Audio bytes
        """
        result = await self.synthesize(text, voice_id, **kwargs)
        return result.audio_data

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
        """
        print(f"DEBUG: Mock TTS: Streaming text: '{text[:50]}...'")

        # Get the complete audio
        audio_data = await self.convert_text(text, voice_id, **kwargs)

        # Split it into chunks to simulate streaming
        chunk_size = 1024
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i : i + chunk_size]
            yield chunk
            await asyncio.sleep(0.1)  # Simulate delay

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        print("DEBUG: Mock TTS: Cleaning up resources")
        self._initialized = False
