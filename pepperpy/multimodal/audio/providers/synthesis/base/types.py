"""Type definitions for audio synthesis providers.

This module defines the types used by audio synthesis providers.
"""

from pathlib import Path
from typing import Any, Protocol, Union

from pepperpy.multimodal.audio.providers.synthesis.base.base import AudioData


class SynthesisProvider(Protocol):
    """Protocol defining the interface for synthesis providers."""

    async def synthesize(self, text: str, **kwargs: Any) -> AudioData:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize
            **kwargs: Additional provider-specific parameters

        Returns:
            Synthesized audio data

        Raises:
            SynthesisError: If synthesis fails

        """
        ...

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
        ...
