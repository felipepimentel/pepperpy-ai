"""Audio format handlers for the unified format handling system.

This module provides format handlers for audio formats:
- WAVFormat: WAV audio format
- MP3Format: MP3 audio format
- FLACFormat: FLAC audio format
- OGGFormat: OGG audio format
"""

from typing import Any, Dict, Optional

try:
    import numpy as np
    from numpy.typing import NDArray

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from .base import FormatError, FormatHandler


class AudioData:
    """Container for audio data."""

    def __init__(
        self,
        samples: Any,  # NDArray if numpy is available, else bytes
        sample_rate: int,
        channels: int = 1,
        bit_depth: int = 16,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize audio data.

        Args:
            samples: Audio samples
            sample_rate: Sample rate in Hz
            channels: Number of channels
            bit_depth: Bit depth
            metadata: Optional metadata
        """
        self.samples = samples
        self.sample_rate = sample_rate
        self.channels = channels
        self.bit_depth = bit_depth
        self.metadata = metadata or {}

    @property
    def duration(self) -> float:
        """Get audio duration in seconds.

        Returns:
            Duration in seconds
        """
        if NUMPY_AVAILABLE and isinstance(self.samples, np.ndarray):
            return len(self.samples) / self.sample_rate / self.channels
        elif isinstance(self.samples, bytes):
            # Approximate duration based on bit depth and channels
            bytes_per_sample = self.bit_depth // 8
            return (
                len(self.samples) / bytes_per_sample / self.channels / self.sample_rate
            )
        return 0.0


class WAVFormat(FormatHandler[AudioData]):
    """Handler for WAV audio format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string
        """
        return "audio/wav"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)
        """
        return ["wav", "wave"]

    def serialize(self, data: AudioData) -> bytes:
        """Serialize AudioData to WAV bytes.

        Args:
            data: AudioData to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you would use a library like wave or scipy
            if isinstance(data.samples, bytes):
                # If already bytes, add WAV header
                return (
                    self._create_wav_header(
                        data.sample_rate,
                        data.channels,
                        data.bit_depth,
                        len(data.samples),
                    )
                    + data.samples
                )
            elif NUMPY_AVAILABLE and isinstance(data.samples, np.ndarray):
                # Convert numpy array to bytes
                if data.samples.dtype == np.float32 or data.samples.dtype == np.float64:
                    # Convert float to int
                    samples_int = (
                        data.samples * (2 ** (data.bit_depth - 1) - 1)
                    ).astype(np.int16 if data.bit_depth <= 16 else np.int32)
                    samples_bytes = samples_int.tobytes()
                else:
                    samples_bytes = data.samples.tobytes()

                return (
                    self._create_wav_header(
                        data.sample_rate,
                        data.channels,
                        data.bit_depth,
                        len(samples_bytes),
                    )
                    + samples_bytes
                )
            else:
                raise FormatError("Unsupported sample format")
        except Exception as e:
            raise FormatError(f"Failed to serialize WAV: {str(e)}") from e

    def deserialize(self, data: bytes) -> AudioData:
        """Deserialize bytes to AudioData.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized AudioData

        Raises:
            FormatError: If deserialization fails
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you would use a library like wave or scipy
            if len(data) < 44:  # Minimum WAV header size
                raise FormatError("Invalid WAV data: too short")

            # Parse WAV header
            if data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
                raise FormatError("Invalid WAV header")

            # Extract format information from header
            sample_rate = int.from_bytes(data[24:28], byteorder="little")
            channels = int.from_bytes(data[22:24], byteorder="little")
            bit_depth = int.from_bytes(data[34:36], byteorder="little")

            # Extract audio data
            audio_data = data[44:]

            # Convert to numpy array if available
            if NUMPY_AVAILABLE:
                dtype = np.int16 if bit_depth <= 16 else np.int32
                samples = np.frombuffer(audio_data, dtype=dtype)
                if channels > 1:
                    samples = samples.reshape(-1, channels)
            else:
                samples = audio_data

            return AudioData(
                samples=samples,
                sample_rate=sample_rate,
                channels=channels,
                bit_depth=bit_depth,
                metadata={"format": "wav"},
            )
        except Exception as e:
            if not isinstance(e, FormatError):
                e = FormatError(f"Failed to deserialize WAV: {str(e)}")
            raise e

    def _create_wav_header(
        self, sample_rate: int, channels: int, bit_depth: int, data_size: int
    ) -> bytes:
        """Create a WAV header.

        Args:
            sample_rate: Sample rate in Hz
            channels: Number of channels
            bit_depth: Bit depth
            data_size: Size of audio data in bytes

        Returns:
            WAV header as bytes
        """
        # Simplified WAV header creation
        header = bytearray()
        # RIFF header
        header.extend(b"RIFF")
        header.extend((data_size + 36).to_bytes(4, byteorder="little"))  # File size - 8
        header.extend(b"WAVE")
        # Format chunk
        header.extend(b"fmt ")
        header.extend((16).to_bytes(4, byteorder="little"))  # Chunk size
        header.extend((1).to_bytes(2, byteorder="little"))  # Format code (1 = PCM)
        header.extend(channels.to_bytes(2, byteorder="little"))  # Channels
        header.extend(sample_rate.to_bytes(4, byteorder="little"))  # Sample rate
        bytes_per_second = sample_rate * channels * (bit_depth // 8)
        header.extend(
            bytes_per_second.to_bytes(4, byteorder="little")
        )  # Bytes per second
        block_align = channels * (bit_depth // 8)
        header.extend(block_align.to_bytes(2, byteorder="little"))  # Block align
        header.extend(bit_depth.to_bytes(2, byteorder="little"))  # Bits per sample
        # Data chunk
        header.extend(b"data")
        header.extend(data_size.to_bytes(4, byteorder="little"))  # Data size
        return bytes(header)


class MP3Format(FormatHandler[AudioData]):
    """Handler for MP3 audio format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string
        """
        return "audio/mp3"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)
        """
        return ["mp3"]

    def serialize(self, data: AudioData) -> bytes:
        """Serialize AudioData to MP3 bytes.

        Args:
            data: AudioData to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails
        """
        # This is a placeholder implementation
        # In a real implementation, you would use a library like pydub or lameenc
        raise FormatError("MP3 serialization requires additional libraries")

    def deserialize(self, data: bytes) -> AudioData:
        """Deserialize bytes to AudioData.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized AudioData

        Raises:
            FormatError: If deserialization fails
        """
        # This is a placeholder implementation
        # In a real implementation, you would use a library like pydub or lameenc
        raise FormatError("MP3 deserialization requires additional libraries")


class FLACFormat(FormatHandler[AudioData]):
    """Handler for FLAC audio format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string
        """
        return "audio/flac"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)
        """
        return ["flac"]

    def serialize(self, data: AudioData) -> bytes:
        """Serialize AudioData to FLAC bytes.

        Args:
            data: AudioData to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails
        """
        # This is a placeholder implementation
        # In a real implementation, you would use a library like pydub or soundfile
        raise FormatError("FLAC serialization requires additional libraries")

    def deserialize(self, data: bytes) -> AudioData:
        """Deserialize bytes to AudioData.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized AudioData

        Raises:
            FormatError: If deserialization fails
        """
        # This is a placeholder implementation
        # In a real implementation, you would use a library like pydub or soundfile
        raise FormatError("FLAC deserialization requires additional libraries")


class OGGFormat(FormatHandler[AudioData]):
    """Handler for OGG audio format."""

    @property
    def mime_type(self) -> str:
        """Get the MIME type for this format.

        Returns:
            MIME type string
        """
        return "audio/ogg"

    @property
    def file_extensions(self) -> list[str]:
        """Get the file extensions for this format.

        Returns:
            List of file extensions (without dot)
        """
        return ["ogg"]

    def serialize(self, data: AudioData) -> bytes:
        """Serialize AudioData to OGG bytes.

        Args:
            data: AudioData to serialize

        Returns:
            Serialized data as bytes

        Raises:
            FormatError: If serialization fails
        """
        # This is a placeholder implementation
        # In a real implementation, you would use a library like pydub or soundfile
        raise FormatError("OGG serialization requires additional libraries")

    def deserialize(self, data: bytes) -> AudioData:
        """Deserialize bytes to AudioData.

        Args:
            data: Bytes to deserialize

        Returns:
            Deserialized AudioData

        Raises:
            FormatError: If deserialization fails
        """
        # This is a placeholder implementation
        # In a real implementation, you would use a library like pydub or soundfile
        raise FormatError("OGG deserialization requires additional libraries")
