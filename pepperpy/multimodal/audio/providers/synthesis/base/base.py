"""Base classes for audio synthesis providers."""

from pathlib import Path
from typing import Any, Optional, Union

from pydantic import Field

from pepperpy.multimodal.audio.base import AudioConfig as BaseAudioConfig
from pepperpy.multimodal.audio.base import AudioData as BaseAudioData
from pepperpy.multimodal.synthesis.base import SynthesisError as BaseSynthesisError
from pepperpy.multimodal.synthesis.base import (
    SynthesisProvider as BaseSynthesisProvider,
)


class AudioConfig(BaseAudioConfig):
    """Audio configuration for synthesis."""

    language: str = Field(default="en", description="Language code")
    voice: Optional[str] = Field(default=None, description="Voice identifier")
    format: str = Field(default="mp3", description="Audio format")
    sample_rate: int = Field(default=24000, description="Sample rate in Hz")
    bit_depth: int = Field(default=16, description="Bit depth")
    channels: int = Field(default=1, description="Number of audio channels")


class AudioData(BaseAudioData):
    """Audio data container."""

    content: bytes = Field(..., description="Audio content as bytes")
    config: AudioConfig = Field(..., description="Audio configuration")
    duration: float = Field(default=0.0, description="Audio duration in seconds")
    size: int = Field(default=0, description="Size in bytes")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class SynthesisError(BaseSynthesisError):
    """Error raised during audio synthesis."""

    pass


class SynthesisProvider(BaseSynthesisProvider):
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
            path: Path to save to
            **kwargs: Additional parameters

        Returns:
            Path to saved file

        Raises:
            SynthesisError: If saving fails
        """
        try:
            # Convert to Path
            path_obj = Path(path)
            
            # Create directory if it doesn't exist
            if not path_obj.parent.exists():
                path_obj.parent.mkdir(parents=True)
            
            # Write audio data to file
            with open(path_obj, "wb") as f:
                f.write(audio.content)
            
            return path_obj
            
        except Exception as e:
            raise SynthesisError(
                "Failed to save audio file",
                details={"error": str(e), "path": str(path)},
            ) from e
