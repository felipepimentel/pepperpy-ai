"""OpenAI provider for speech synthesis capability."""

import os
from typing import Any, Literal, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from .base import AudioConfig, AudioData, BaseSynthesisProvider, SynthesisError


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI synthesis provider."""

    api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key. If not provided, uses OPENAI_API_KEY environment variable.",
    )
    model: str = Field(
        default="tts-1", description="Model to use for speech synthesis."
    )
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = Field(
        default="alloy", description="Voice to use for synthesis."
    )
    output_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = Field(
        default="mp3", description="Audio format to generate."
    )


class OpenAISynthesisProvider(BaseSynthesisProvider):
    """OpenAI implementation of speech synthesis provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "tts-1",
        voice: str = "alloy",
        output_format: str = "mp3",
    ):
        """Initialize OpenAI synthesis provider.

        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY environment variable.
            model: Model to use for speech synthesis.
            voice: Voice to use for synthesis.
            output_format: Audio format to generate.
        """
        self.config = OpenAIConfig(
            api_key=api_key,
            model=model,
            voice=voice,
            output_format=output_format,
        )
        self.client = AsyncOpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    async def synthesize(
        self,
        text: str,
        *,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioData:
        """Synthesize text to speech using OpenAI's API.

        Args:
            text: Text to synthesize
            language: Optional language code (not used by OpenAI)
            voice: Optional voice identifier (overrides the default)
            **kwargs: Additional parameters to pass to the API

        Returns:
            Synthesized audio data

        Raises:
            SynthesisError: If synthesis fails
        """
        try:
            # Use provided voice or default from config
            voice_id = voice or self.config.voice

            # Call OpenAI API
            response = await self.client.audio.speech.create(
                model=self.config.model,
                voice=voice_id,
                input=text,
                response_format=self.config.output_format,
                **kwargs,
            )

            # Get audio content
            audio_content = await response.read()

            # Create audio config
            config = AudioConfig(
                language=language or "en",
                voice=voice_id,
                format=self.config.output_format,
                sample_rate=24000,  # OpenAI uses 24kHz
                bit_depth=16,
                channels=1,
                metadata={
                    "model": self.config.model,
                    "provider": "openai",
                },
            )

            # Create audio data
            return AudioData(
                content=audio_content,
                config=config,
                duration=len(audio_content) / (24000 * 2),  # Approximate duration
                size=len(audio_content),
                metadata={
                    "model": self.config.model,
                    "provider": "openai",
                    "voice": voice_id,
                },
            )

        except Exception as e:
            raise SynthesisError(
                f"OpenAI synthesis failed: {str(e)}",
                provider="openai",
                details={"error": str(e), "model": self.config.model},
            )
