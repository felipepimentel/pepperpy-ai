"""Base classes and interfaces for the unified audio processing system.

This module provides the core abstractions for the audio processing system:
- AudioFeatures: Container for extracted features from audio
- BaseAudioProcessor: Base class for all audio processors
"""

from abc import abstractmethod
from dataclasses import dataclass
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

from ..core.base.common import BaseComponent


@dataclass
class AudioFeatures:
    """Represents extracted features from an audio signal."""

    features: Union[List[float], "np.ndarray"] if NUMPY_AVAILABLE else List[float]
    sample_rate: int
    duration: float
    metadata: Optional[Dict[str, Any]] = None


class BaseAudioProcessor(BaseComponent):
    """Base class for all audio processors."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize audio processor.

        Args:
            name: Processor name
            config: Optional configuration
        """
        super().__init__(name)
        self._config = config or {}
        self._sample_rate = self._config.get("sample_rate", 44100)

    @abstractmethod
    async def process(self, audio: Any) -> Any:
        """Process audio data.

        Args:
            audio: Input audio array

        Returns:
            Processed audio array
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
