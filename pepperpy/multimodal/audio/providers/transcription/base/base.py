"""Base classes for audio transcription providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""

    text: str
    confidence: float
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TranscriptionSegment:
    """Segment of transcribed audio with timing information."""

    text: str
    start_time: float
    end_time: float
    confidence: float
    language: Optional[str] = None
    speaker: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TranscriptionError(Exception):
    """Exception raised for errors in the transcription process."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize transcription error.

        Args:
            message: Error message
            provider: Provider name
            details: Additional error details
        """
        self.provider = provider
        self.details = details or {}
        super().__init__(message)


class TranscriptionProvider(ABC):
    """Base class for speech transcription providers."""

    @abstractmethod
    def transcribe(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Transcribe audio to text.

        Args:
            audio: Path to audio file, audio file bytes, or URL
            language: Optional language code
            **kwargs: Additional provider-specific parameters

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        pass

    def transcribe_with_timestamps(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Union[str, float]]]:
        """Transcribe audio with timestamps.

        Args:
            audio: Path to audio file, audio file bytes, or URL
            language: Optional language code
            **kwargs: Additional provider-specific parameters

        Returns:
            List of segments with text and timestamps

        Raises:
            TranscriptionError: If transcription fails
        """
        raise NotImplementedError(
            "This provider does not support transcription with timestamps"
        )

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes.

        Returns:
            List of language codes
        """
        return []

    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats.

        Returns:
            List of format extensions
        """
        return []
