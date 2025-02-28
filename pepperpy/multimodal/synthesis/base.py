"""Base interfaces for synthesis capability."""

from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ..base import (
    ContentType,
    DataFormat,
    MultimodalError,
    MultimodalProcessor,
    MultimodalProvider,
)


class SynthesisError(MultimodalError):
    """Base class for synthesis-related errors."""

    def __init__(
        self,
        message: str,
        *,
        component: Optional[str] = None,
        provider: Optional[str] = None,
        voice: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            component: Optional component name that caused the error
            provider: Optional provider name that caused the error
            voice: Optional voice that caused the error
            details: Optional additional details
        """
        all_details = details or {}
        if voice:
            all_details["voice"] = voice

        super().__init__(
            message, component=component, provider=provider, details=all_details
        )
        self.voice = voice


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


class SynthesisProvider(MultimodalProvider):
    """Base class for synthesis providers."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        supported_formats: Optional[List[DataFormat]] = None,
    ) -> None:
        """Initialize synthesis provider.

        Args:
            name: Provider name
            config: Optional configuration
            supported_formats: List of supported formats
        """
        if supported_formats is None:
            supported_formats = [
                DataFormat.MP3,
                DataFormat.WAV,
                DataFormat.OGG,
                DataFormat.FLAC,
            ]

        super().__init__(
            name,
            config=config,
            supported_content_types=[ContentType.AUDIO],
            supported_formats=supported_formats,
        )

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        Raises:
            SynthesisError: If initialization fails
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider.

        Raises:
            SynthesisError: If shutdown fails
        """
        pass

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


class SynthesisProcessor(MultimodalProcessor):
    """Base class for synthesis processors."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        supported_formats: Optional[List[DataFormat]] = None,
    ) -> None:
        """Initialize synthesis processor.

        Args:
            name: Processor name
            config: Optional configuration
            supported_formats: List of supported formats
        """
        if supported_formats is None:
            supported_formats = [
                DataFormat.MP3,
                DataFormat.WAV,
                DataFormat.OGG,
                DataFormat.FLAC,
            ]

        super().__init__(
            name,
            config=config,
            supported_content_types=[ContentType.AUDIO],
            supported_formats=supported_formats,
        )

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
