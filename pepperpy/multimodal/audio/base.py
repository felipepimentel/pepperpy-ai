"""Base classes and interfaces for the unified audio processing system.

This module provides the core abstractions for the audio processing system:
- AudioFeatures: Container for extracted features from audio
- AudioProcessor: Base class for all audio processors
- AudioProvider: Base class for audio service providers
"""

from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Try to import numpy, but provide fallbacks if not available
try:
    import numpy as np
    from numpy.typing import NDArray

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

    # Define a simple placeholder for np.ndarray when numpy is not available
    class MockNDArray:
        pass

    np = None
    NDArray = Any

from ..base import (
    ContentType,
    DataFormat,
    MultimodalError,
    MultimodalProcessor,
    MultimodalProvider,
)


class AudioError(MultimodalError):
    """Base exception for audio-related errors."""

    def __init__(
        self,
        message: str,
        *,
        component: Optional[str] = None,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            component: Optional component name that caused the error
            provider: Optional provider name that caused the error
            details: Optional additional details
        """
        super().__init__(
            message, component=component, provider=provider, details=details
        )


@dataclass
class AudioFeatures:
    """Represents extracted features from an audio signal."""

    features: Union[List[float], "np.ndarray"] if NUMPY_AVAILABLE else List[float]
    sample_rate: int
    duration: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Transcription:
    """Represents a transcription of audio to text."""

    text: str
    confidence: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AudioProcessor(MultimodalProcessor):
    """Base class for all audio processors."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        supported_formats: Optional[List[DataFormat]] = None,
    ) -> None:
        """Initialize audio processor.

        Args:
            name: Processor name
            config: Optional configuration
            supported_formats: List of supported audio formats
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
        self._sample_rate = self._config.get("sample_rate", 44100)

    @abstractmethod
    async def process(self, audio: Any) -> Any:
        """Process audio data.

        Args:
            audio: Input audio array

        Returns:
            Processed audio array

        Raises:
            AudioError: If processing fails
        """
        pass

    def _normalize(self, audio: Any) -> Any:
        """Normalize audio levels.

        Args:
            audio: Input audio array

        Returns:
            Normalized audio array
        """
        if not NUMPY_AVAILABLE:
            # Simple normalization for non-numpy arrays
            if not audio:
                return audio
            max_val = max(abs(x) for x in audio)
            if max_val > 0:
                return [x / max_val for x in audio]
            return audio
        else:
            # Scale to [-1, 1] range using numpy
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                return audio / max_val
            return audio


class AudioProvider(MultimodalProvider):
    """Base class for audio service providers."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        supported_formats: Optional[List[DataFormat]] = None,
    ) -> None:
        """Initialize audio provider.

        Args:
            name: Provider name
            config: Optional configuration
            supported_formats: List of supported audio formats
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
            AudioError: If initialization fails
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider.

        Raises:
            AudioError: If shutdown fails
        """
        pass

    async def save_audio(
        self, audio: Any, path: Union[str, Path], format: Optional[DataFormat] = None
    ) -> Path:
        """Save audio data to file.

        Args:
            audio: Audio data to save
            path: Output file path
            format: Optional output format

        Returns:
            Path to saved file

        Raises:
            AudioError: If saving fails
        """
        raise NotImplementedError("save_audio method must be implemented by subclasses")
