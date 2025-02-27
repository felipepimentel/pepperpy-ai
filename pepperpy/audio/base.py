"""Base classes and interfaces for the unified audio processing system.

This module provides the core abstractions for the audio processing system:
- AudioFeatures: Container for extracted features from audio
- BaseAudioProcessor: Base class for all audio processors
"""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
from numpy.typing import NDArray

from ..core.base.common import BaseComponent


@dataclass
class AudioFeatures:
    """Represents extracted features from an audio signal."""

    features: np.ndarray
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
    async def process(self, audio: NDArray) -> NDArray:
        """Process audio data.

        Args:
            audio: Input audio array

        Returns:
            Processed audio array
        """
        pass

    def _normalize(self, audio: NDArray) -> NDArray:
        """Normalize audio levels.

        Args:
            audio: Input audio array

        Returns:
            Normalized audio array
        """
        # Scale to [-1, 1] range
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio
