"""Base interfaces for speech synthesis capability."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional


class BaseSynthesisProvider(ABC):
    """Base class for speech synthesis providers."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        *,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        output_format: str = "mp3",
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
        pass

    @abstractmethod
    async def save(
        self,
        audio_data: bytes,
        output_path: Path,
        *,
        processors: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Path:
        """Save synthesized audio to file with optional processing.

        Args:
            audio_data: Audio data to save
            output_path: Path to save the file
            processors: Audio processors to apply
            **kwargs: Additional processor-specific parameters

        Returns:
            Path to the saved file
        """
        pass

    @abstractmethod
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
        pass
