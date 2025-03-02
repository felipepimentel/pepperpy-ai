"""Base classes for audio synthesis providers.

This module provides base classes for audio synthesis providers that extend
the general multimodal synthesis framework.
"""

from pathlib import Path
from typing import Any, Union

from pepperpy.multimodal.synthesis.base import (
    AudioConfig as BaseAudioConfig,
)
from pepperpy.multimodal.synthesis.base import (
    AudioData as BaseAudioData,
)
from pepperpy.multimodal.synthesis.base import (
    SynthesisError as BaseSynthesisError,
)
from pepperpy.multimodal.synthesis.base import (
    SynthesisProvider as BaseSynthesisProvider,
)


class AudioConfig(BaseAudioConfig):
    """Configuration for audio synthesis.

    Extends the base AudioConfig from multimodal synthesis.
    """

    pass


class AudioData(BaseAudioData):
    """Container for synthesized audio data.

    Extends the base AudioData from multimodal synthesis.
    """

    pass


class SynthesisError(BaseSynthesisError):
    """Exception raised for errors in the synthesis process.

    Extends the base SynthesisError from multimodal synthesis.
    """

    pass


class SynthesisProvider(BaseSynthesisProvider):
    """Base class for speech synthesis providers.

    Extends the base SynthesisProvider from multimodal synthesis.
    """

    pass


class BaseSynthesisProvider(SynthesisProvider):
    """Base implementation of synthesis provider with common functionality."""

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
