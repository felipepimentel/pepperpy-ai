"""Audio effects processor for synthesis capability."""

import io
from typing import Any, List, Optional, Union

# pip install pydantic
try:
    from pydantic import BaseModel, Field
except ImportError:
    print("Pydantic not installed. Install with: pip install pydantic")
    BaseModel = object
    
    def Field(*args, **kwargs):
        def decorator(x):
            return x
        return decorator

# pip install pydub
try:
    from pydub import AudioSegment
except ImportError:
    print("Pydub not installed. Install with: pip install pydub")

    class AudioSegment:
        pass


from pepperpy.multimodal.synthesis.base import AudioData, AudioProcessor, SynthesisError


class AudioEffectsConfig(BaseModel):
    """Configuration for audio effects processor."""

    normalize: bool = Field(default=True, description="Normalize audio volume")
    target_db: float = Field(default=-20.0, description="Target dB for normalization")
    fade_in: Optional[float] = Field(
        default=None, description="Fade in duration in seconds"
    )
    fade_out: Optional[float] = Field(
        default=None, description="Fade out duration in seconds"
    )
    speed: float = Field(default=1.0, description="Playback speed multiplier (0.5-2.0)")
    pitch: float = Field(
        default=0.0, description="Pitch shift in semitones (-12 to 12)"
    )


class AudioEffectsProcessor(AudioProcessor):
    """Audio effects processor implementation."""

    def __init__(self, **config: Any):
        """Initialize processor with configuration.

        Args:
            **config: Configuration parameters

        Raises:
            SynthesisError: If configuration is invalid
        """
        try:
            self.config = AudioEffectsConfig(**config)
        except Exception as e:
            raise SynthesisError(
                "Failed to initialize audio effects processor",
                details={"error": str(e)},
            ) from e

    async def process(
        self,
        audio: Union[AudioData, List[AudioData]],
        **kwargs: Any,
    ) -> Union[AudioData, List[AudioData]]:
        """Process audio data with effects.

        Args:
            audio: Single audio data or list to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Processed audio data

        Raises:
            SynthesisError: If processing fails
        """
        try:
            # Convert single item to list for uniform processing
            audio_list = [audio] if isinstance(audio, AudioData) else audio

            processed = []
            for item in audio_list:
                # Load audio data
                segment = AudioSegment.from_file(
                    io.BytesIO(item.content),
                    format=item.config.format,
                )

                # Apply effects
                if self.config.normalize:
                    segment = segment.normalize(headroom=abs(self.config.target_db))

                if self.config.fade_in:
                    segment = segment.fade_in(int(self.config.fade_in * 1000))

                if self.config.fade_out:
                    segment = segment.fade_out(int(self.config.fade_out * 1000))

                if self.config.speed != 1.0:
                    # Change tempo without affecting pitch
                    segment = segment.speedup(playback_speed=self.config.speed)

                if self.config.pitch != 0.0:
                    # Shift pitch without affecting tempo
                    segment = segment._spawn(
                        segment.raw_data,
                        overrides={
                            "frame_rate": int(
                                segment.frame_rate * (2 ** (self.config.pitch / 12))
                            )
                        },
                    )

                # Export processed audio
                buffer = io.BytesIO()
                segment.export(
                    buffer,
                    format=item.config.format,
                    parameters=[
                        "-ar",
                        str(item.config.sample_rate),
                        "-ac",
                        str(item.config.channels),
                    ],
                )

                # Create new audio data
                processed_item = AudioData(
                    content=buffer.getvalue(),
                    config=item.config,
                    duration=len(segment) / 1000.0,  # Convert ms to seconds
                    size=len(buffer.getvalue()),
                    metadata={
                        **item.metadata,
                        "effects": {
                            "normalized": self.config.normalize,
                            "target_db": self.config.target_db,
                            "fade_in": self.config.fade_in,
                            "fade_out": self.config.fade_out,
                            "speed": self.config.speed,
                            "pitch": self.config.pitch,
                        },
                    },
                )
                processed.append(processed_item)

            # Return single item or list based on input type
            return processed[0] if isinstance(audio, AudioData) else processed

        except Exception as e:
            raise SynthesisError(
                "Failed to process audio",
                details={"error": str(e)},
            ) from e
