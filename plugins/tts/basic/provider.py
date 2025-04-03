"""Basic TTS provider implementation for PepperPy.

This module provides a basic text-to-speech provider using system voices via pyttsx3.
"""

import asyncio
import os
import tempfile
from typing import Any, List, Optional

import pyttsx3

from pepperpy.plugin import ProviderPlugin
from pepperpy.tts.base import (
    TTSAudio as SpeechResult,
)
from pepperpy.tts.base import (
    TTSProvider,
)
from pepperpy.tts.base import (
    TTSVoice as Voice,
)


class BasicTTSProvider(TTSProvider, ProviderPlugin):
    """Basic text-to-speech provider using system voices.

    This provider integrates with pyttsx3 to provide access to system TTS voices.
    """

    # Type-annotated config attributes that match plugin.yaml schema
    voice: str = "default"
    rate: float = 1.0
    volume: float = 1.0
    pitch: float = 1.0
    format: str = "wav"

    def __init__(self) -> None:
        """Initialize the provider."""
        super().__init__()
        self.engine: Optional[pyttsx3.Engine] = None
        self.available_voices: List[Voice] = []

    async def initialize(self) -> None:
        """Initialize the TTS engine.

        This is called automatically when the provider is first used.
        """
        if self.initialized:
            return

        # Create engine in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._init_engine)

        self.initialized = True
        self.logger.debug("TTS engine initialized")

    def _init_engine(self) -> None:
        """Initialize the pyttsx3 engine in a separate thread."""
        try:
            self.engine = pyttsx3.init()

            # Only configure if engine was successfully initialized
            if self.engine:
                # Configure engine
                self.engine.setProperty("rate", self.rate * 200)  # Base rate is 200
                self.engine.setProperty("volume", self.volume)

                # Set voice if specified
                if self.voice != "default":
                    voices = self.engine.getProperty("voices")
                    for v in voices:
                        if self.voice in (v.id, v.name):
                            self.engine.setProperty("voice", v.id)
                            break

                # Load available voices
                self._load_voices()

        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            raise

    def _load_voices(self) -> None:
        """Load available voices from the engine."""
        if not self.engine:
            return

        try:
            engine_voices = self.engine.getProperty("voices")
            self.available_voices = [
                Voice(
                    id=v.id,
                    name=v.name,
                    gender=getattr(v, "gender", "unknown"),
                    language=getattr(v, "language", None),
                )
                for v in engine_voices
            ]

            self.logger.debug(f"Loaded {len(self.available_voices)} voices")
        except Exception as e:
            self.logger.warning(f"Failed to load voices: {e}")

    async def cleanup(self) -> None:
        """Clean up resources.

        This is called automatically when the context manager exits.
        """
        if self.engine:
            # Run cleanup in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._cleanup_engine)

            self.engine = None

        self.initialized = False
        self.logger.debug("Resources cleaned up")

    def _cleanup_engine(self) -> None:
        """Clean up the pyttsx3 engine in a separate thread."""
        if self.engine:
            try:
                self.engine.stop()
            except Exception as e:
                self.logger.warning(f"Error stopping TTS engine: {e}")

    async def get_available_voices(self) -> List[Voice]:
        """Get available voices.

        Returns:
            List of available voices
        """
        if not self.initialized:
            await self.initialize()

        return self.available_voices

    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs: Any,
    ) -> SpeechResult:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize
            voice_id: Voice ID to use
            output_path: Path to save output file (optional)
            **kwargs: Additional synthesis options

        Returns:
            SpeechResult with audio data and metadata

        Raises:
            Exception: If synthesis fails
        """
        if not self.initialized:
            await self.initialize()

        if not self.engine:
            raise RuntimeError("TTS engine not initialized")

        # Prepare synthesis options
        actual_voice_id = voice_id or kwargs.get("voice_id", self.voice)
        if actual_voice_id is None:
            actual_voice_id = "default"  # Fallback to default if still None

        rate = kwargs.get("rate", self.rate)
        volume = kwargs.get("volume", self.volume)
        output_format = kwargs.get("format", self.format)

        # Create temp file for output if not provided
        temp_file = None
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f".{output_format}", delete=False
            )
            output_path = temp_file.name
            temp_file.close()

        # Synthesize in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._synthesize_to_file(
                text, output_path, actual_voice_id, rate, volume
            ),
        )

        # Read the resulting file
        with open(output_path, "rb") as f:
            audio_data = f.read()

        # Clean up temp file if we created it
        if temp_file:
            try:
                os.unlink(output_path)
            except Exception:
                pass

        # Return the result
        return SpeechResult(
            audio_data=audio_data,
            content_type=f"audio/{output_format}",
            duration_seconds=None,  # We don't know the duration
        )

    def _synthesize_to_file(
        self, text: str, output_path: str, voice_id: str, rate: float, volume: float
    ) -> None:
        """Synthesize speech to a file using pyttsx3.

        Args:
            text: Text to synthesize
            output_path: Path to save the audio file
            voice_id: ID of voice to use
            rate: Speaking rate multiplier
            volume: Volume level

        Raises:
            Exception: If synthesis fails
        """
        if not self.engine:
            raise RuntimeError("TTS engine not initialized")

        # Configure engine for this synthesis
        self.engine.setProperty("rate", rate * 200)  # Base rate is 200
        self.engine.setProperty("volume", volume)

        # Set voice if different from current
        if voice_id != "default":
            voices = self.engine.getProperty("voices")
            for v in voices:
                if voice_id in (v.id, v.name):
                    self.engine.setProperty("voice", v.id)
                    break

        # Save to file
        self.engine.save_to_file(text, output_path)
        self.engine.runAndWait()
