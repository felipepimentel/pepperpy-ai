"""Base classes for audio synthesis providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union


@dataclass
class AudioConfig:
    """Configuration for audio synthesis."""

    language: str
    voice: str
    format: str
    sample_rate: int
    bit_depth: int
    channels: int
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AudioData:
    """Container for synthesized audio data."""

    content: bytes
    config: AudioConfig
    duration: float
    size: int
    metadata: Optional[Dict[str, Any]] = None


class SynthesisError(Exception):
    """Exception raised for errors in the synthesis process."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize synthesis error.

        Args:
            message: Error message
            provider: Provider name
            details: Additional error details
        """
        self.provider = provider
        self.details = details or {}
        super().__init__(message)


class SynthesisProvider(ABC):
    """Base class for speech synthesis providers."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        *,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioData:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize
            language: Optional language code
            voice: Optional voice identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            Synthesized audio data

        Raises:
            SynthesisError: If synthesis fails
        """
        pass

    @abstractmethod
    async def save(
        self,
        audio: AudioData,
        path: Union[str, Path],
        **kwargs: Any,
    ) -> Path:
        """Save audio data to file.

        Args:
            audio: Audio data to save
            path: Output file path
            **kwargs: Additional provider-specific parameters

        Returns:
            Path to saved file

        Raises:
            SynthesisError: If saving fails
        """
        pass


class BaseSynthesisProvider(SynthesisProvider):
    """Base implementation of synthesis provider with common functionality."""

    async def synthesize(
        self,
        text: str,
        *,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioData:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize
            language: Optional language code
            voice: Optional voice identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            Synthesized audio data

        Raises:
            SynthesisError: If synthesis fails
        """
        raise NotImplementedError("Subclasses must implement synthesize method")

    async def save(
        self,
        audio: AudioData,
        path: Union[str, Path],
        **kwargs: Any,
    ) -> Path:
        """Save audio data to file.

        Args:
            audio: Audio data to save
            path: Output file path
            **kwargs: Additional provider-specific parameters

        Returns:
            Path to saved file

        Raises:
            SynthesisError: If saving fails
        """
        try:
            # Convert path to Path object
            output_path = Path(path)

            # Create parent directories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write audio data
            output_path.write_bytes(audio.content)

            return output_path

        except Exception as e:
            raise SynthesisError(
                "Failed to save audio file",
                details={"error": str(e), "path": str(path)},
            )
