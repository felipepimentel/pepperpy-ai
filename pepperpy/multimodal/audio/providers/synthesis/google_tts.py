"""Google Text-to-Speech provider for synthesis capability."""

import asyncio
import io
from pathlib import Path
from typing import Any, Optional, Union

from gtts import gTTS
from pydantic import BaseModel, Field

from pepperpy.multimodal.audio.base import (
    AudioConfig,
    AudioData,
    SynthesisError,
    SynthesisProvider,
)


class GTTSConfig(BaseModel):
    """Configuration for gTTS provider."""

    language: str = Field(default="en", description="Default language code")
    slow: bool = Field(default=False, description="Slow speech rate")
    format: str = Field(default="mp3", description="Output audio format")
    sample_rate: int = Field(default=24000, description="Sample rate in Hz")
    bit_depth: int = Field(default=16, description="Bit depth")
    channels: int = Field(default=1, description="Number of audio channels")


class GTTSProvider(SynthesisProvider):
    """Google Text-to-Speech implementation."""

    def __init__(self, **config: Any):
        """Initialize provider with configuration.

        Args:
            **config: Configuration parameters

        Raises:
            SynthesisError: If configuration is invalid

        """
        try:
            self.config = GTTSConfig(**config)
        except Exception as e:
            raise SynthesisError(
                "Failed to initialize gTTS provider",
                provider="gtts",
                details={"error": str(e)},
            ) from e

    async def synthesize(
        self,
        text: str,
        *,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioData:
        """Synthesize text to speech using gTTS.

        Args:
            text: Text to synthesize
            language: Language code (overrides config)
            voice: Voice name (not used by gTTS)
            **kwargs: Additional parameters

        Returns:
            AudioData object with synthesized speech

        Raises:
            SynthesisError: If synthesis fails

        """
        try:
            # Run gTTS in executor (blocking operation)
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_sync,
                text,
                language or self.config.language,
                kwargs.get("slow", self.config.slow),
            )

            # Create audio configuration
            config = AudioConfig(
                language=language or self.config.language,
                voice="default",  # gTTS doesn't support voice selection
                format=self.config.format,
                sample_rate=self.config.sample_rate,
                bit_depth=self.config.bit_depth,
                channels=self.config.channels,
            )

            # Return audio data
            return AudioData(
                content=audio_data,
                config=config,
                duration=0.0,  # gTTS doesn't provide duration info
                size=len(audio_data),
                metadata={
                    "provider": "gtts",
                    "slow": kwargs.get("slow", self.config.slow),
                },
            )

        except Exception as e:
            raise SynthesisError(
                "Failed to synthesize speech",
                provider="gtts",
                details={"error": str(e), "text": text},
            ) from e

    def _synthesize_sync(self, text: str, language: str, slow: bool) -> bytes:
        """Synchronous gTTS synthesis.

        Args:
            text: Text to synthesize
            language: Language code
            slow: Whether to use slow speech rate

        Returns:
            Audio data as bytes

        """
        # Create gTTS instance
        tts = gTTS(text=text, lang=language, slow=slow)

        # Save to buffer
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)

        return buffer.getvalue()

    async def save(
        self,
        audio: AudioData,
        path: Union[str, Path],
        **kwargs: Any,
    ) -> Path:
        """Save audio data to file.

        Args:
            audio: Audio data to save
            path: Path to save to
            **kwargs: Additional parameters

        Returns:
            Path to saved file

        Raises:
            SynthesisError: If saving fails

        """
        try:
            # Convert to Path
            path_obj = Path(path)

            # Create directory if it doesn't exist
            if not path_obj.parent.exists():
                path_obj.parent.mkdir(parents=True)

            # Write audio data to file
            with open(path_obj, "wb") as f:
                f.write(audio.content)

            return path_obj

        except Exception as e:
            raise SynthesisError(
                "Failed to save audio file",
                provider="gtts",
                details={"error": str(e), "path": str(path)},
            ) from e
