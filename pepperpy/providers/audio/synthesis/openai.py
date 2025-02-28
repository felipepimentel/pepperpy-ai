"""OpenAI provider for speech synthesis capability."""

import os
from pathlib import Path
from typing import Any, BinaryIO, Dict, Literal, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from pepperpy.audio.providers.synthesis.base import BaseSynthesisProvider


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


class OpenAIProvider(BaseSynthesisProvider):
    """OpenAI implementation of speech synthesis provider."""

    def __init__(self, **config: Any):
        """Initialize provider with configuration.

        Args:
            **config: Configuration parameters
        """
        self.config = OpenAIConfig(**config)
        self.client = AsyncOpenAI(
            api_key=self.config.api_key or os.getenv("OPENAI_API_KEY")
        )

    async def synthesize(
        self,
        text: str,
        *,
        voice: Optional[
            Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        ] = None,
        language: Optional[str] = None,
        output_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "mp3",
        **kwargs: Any,
    ) -> bytes:
        """Synthesize speech from text.

        Args:
            text: Input text to synthesize
            voice: Voice identifier to use
            language: Language code (e.g. 'pt-BR')
            output_format: Audio format to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Audio data as bytes
        """
        response = await self.client.audio.speech.create(
            model=self.config.model,
            voice=voice or self.config.voice,
            input=text,
            response_format=output_format,
            **kwargs,
        )
        return response.content

    async def save(
        self,
        audio_data: bytes,
        output_path: Path,
        *,
        processors: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Path:
        """Save synthesized audio to file.

        Args:
            audio_data: Audio data to save
            output_path: Path to save the file
            processors: Audio processors to apply
            **kwargs: Additional processor-specific parameters

        Returns:
            Path to the saved file
        """
        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save file
        with open(output_path, "wb") as f:
            f.write(audio_data)

        return output_path

    async def stream(
        self,
        text: str,
        output_stream: BinaryIO,
        *,
        chunk_size: int = 1024,
        **kwargs: Any,
    ) -> None:
        """Stream synthesized speech to an output stream.

        Args:
            text: Input text to synthesize
            output_stream: Stream to write audio data to
            chunk_size: Size of audio chunks to stream
            **kwargs: Additional provider-specific parameters
        """
        # Generate audio
        audio_data = await self.synthesize(text, **kwargs)

        # Stream in chunks
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i : i + chunk_size]
            output_stream.write(chunk)
