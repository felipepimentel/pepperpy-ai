"""Type definitions for audio transcription providers.

This module defines the types used by audio transcription providers.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union


class TranscriptionProvider(Protocol):
    """Protocol defining the interface for transcription providers."""

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
        ...

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
        ...

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes.

        Returns:
            List of language codes
        """
        ...

    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats.

        Returns:
            List of format extensions
        """
        ...
