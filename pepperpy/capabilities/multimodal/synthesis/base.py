"""Base interfaces for synthesis capability."""

from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from pepperpy.core.common.base import BaseComponent as Processor
from pepperpy.core.common.base import BaseProvider as Provider


class SynthesisError(Exception):
    """Base class for synthesis-related errors."""

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        voice: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            provider: Optional provider name that caused the error
            voice: Optional voice that caused the error
            details: Optional additional details
        """
        super().__init__(message)
        self.provider = provider
        self.voice = voice
        self.details = details or {}


class AudioConfig(BaseModel):
    """Configuration for audio synthesis."""

    language: str = Field(default="en", description="Language code")
    voice: str = Field(default="default", description="Voice identifier")
    rate: float = Field(default=1.0, description="Speech rate (0.5-2.0)")
    pitch: float = Field(default=1.0, description="Voice pitch (-20.0-20.0)")
    volume: float = Field(default=1.0, description="Audio volume (0.0-2.0)")
    format: str = Field(default="mp3", description="Output audio format")
    sample_rate: int = Field(default=24000, description="Sample rate in Hz")
    bit_depth: int = Field(default=16, description="Bit depth")
    channels: int = Field(default=1, description="Number of audio channels")


class AudioData(BaseModel):
    """Represents synthesized audio data."""

    content: bytes = Field(description="Raw audio data")
    config: AudioConfig = Field(description="Audio configuration")
    duration: float = Field(description="Audio duration in seconds")
    size: int = Field(description="Audio size in bytes")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class SynthesisProvider(Provider):
    """Base class for synthesis providers."""

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


class AudioProcessor(Processor):
    """Base class for audio processors."""

    @abstractmethod
    async def process(
        self,
        audio: Union[AudioData, List[AudioData]],
        **kwargs: Any,
    ) -> Union[AudioData, List[AudioData]]:
        """Process audio data.

        Args:
            audio: Single audio data or list to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Processed audio data

        Raises:
            SynthesisError: If processing fails
        """
        pass
