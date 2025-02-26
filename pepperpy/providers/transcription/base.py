"""Base interfaces and exceptions for transcription providers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Union


class TranscriptionError(Exception):
    """Base exception for transcription errors."""

    pass


class TranscriptionProvider(ABC):
    """Base class for transcription providers."""

    @abstractmethod
    def transcribe(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Transcribe audio to text.

        Args:
            audio: Path to audio file, audio file bytes, or URL
            language: Optional language code (e.g. 'en', 'pt')
            **kwargs: Additional provider-specific parameters

        Returns:
            str: Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        pass

    @abstractmethod
    def transcribe_with_timestamps(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Union[str, float]]]:
        """Transcribe audio to text with word/segment timestamps.

        Args:
            audio: Path to audio file, audio file bytes, or URL
            language: Optional language code (e.g. 'en', 'pt')
            **kwargs: Additional provider-specific parameters

        Returns:
            List[Dict[str, Union[str, float]]]: List of segments with text and timestamps

        Raises:
            TranscriptionError: If transcription fails
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes.

        Returns:
            List[str]: List of language codes
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats.

        Returns:
            List[str]: List of format extensions (e.g. ['mp3', 'wav'])
        """
        pass 