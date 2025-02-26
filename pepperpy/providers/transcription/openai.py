"""OpenAI transcription provider implementation."""

from pathlib import Path
from typing import Dict, List, Optional, Union

from pepperpy.providers.transcription.base import TranscriptionProvider, TranscriptionError


class OpenAITranscriptionProvider(TranscriptionProvider):
    """OpenAI transcription provider implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-1",
        **kwargs,
    ):
        """Initialize OpenAI transcription provider.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: whisper-1)
            **kwargs: Additional parameters to pass to OpenAI

        Raises:
            ImportError: If openai package is not installed
            TranscriptionError: If initialization fails
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAITranscriptionProvider. "
                "Install it with: pip install openai"
            )

        self.model = model
        self.kwargs = kwargs

        try:
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            raise TranscriptionError(f"Failed to initialize OpenAI client: {e}")

    def transcribe(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Transcribe audio using OpenAI.

        Args:
            audio: Path to audio file, audio file bytes, or URL
            language: Optional language code (e.g. 'en', 'pt')
            **kwargs: Additional parameters to pass to OpenAI

        Returns:
            str: Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            # Handle different audio input types
            if isinstance(audio, (str, Path)):
                audio_path = Path(audio)
                if not audio_path.exists():
                    raise TranscriptionError(f"Audio file not found: {audio_path}")
                audio_file = open(audio_path, "rb")
            else:
                from io import BytesIO
                audio_file = BytesIO(audio)

            try:
                # Prepare parameters
                params = {
                    "model": self.model,
                    "language": language,
                    **self.kwargs,
                    **kwargs,
                }

                # Remove None values
                params = {k: v for k, v in params.items() if v is not None}

                # Transcribe audio
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **params,
                )

                return response.text

            finally:
                audio_file.close()

        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio: {e}")

    def transcribe_with_timestamps(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Union[str, float]]]:
        """Transcribe audio with timestamps using OpenAI.

        Args:
            audio: Path to audio file, audio file bytes, or URL
            language: Optional language code (e.g. 'en', 'pt')
            **kwargs: Additional parameters to pass to OpenAI

        Returns:
            List[Dict[str, Union[str, float]]]: List of segments with text and timestamps

        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            # Handle different audio input types
            if isinstance(audio, (str, Path)):
                audio_path = Path(audio)
                if not audio_path.exists():
                    raise TranscriptionError(f"Audio file not found: {audio_path}")
                audio_file = open(audio_path, "rb")
            else:
                from io import BytesIO
                audio_file = BytesIO(audio)

            try:
                # Prepare parameters
                params = {
                    "model": self.model,
                    "language": language,
                    "response_format": "verbose_json",
                    **self.kwargs,
                    **kwargs,
                }

                # Remove None values
                params = {k: v for k, v in params.items() if v is not None}

                # Transcribe audio
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **params,
                )

                # Extract segments with timestamps
                segments = []
                for segment in response.segments:
                    segments.append({
                        "text": segment.text,
                        "start": segment.start,
                        "end": segment.end,
                    })

                return segments

            finally:
                audio_file.close()

        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio: {e}")

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes.

        Returns:
            List[str]: List of language codes
        """
        return [
            "af", "ar", "hy", "az", "be", "bs", "bg", "ca", "zh", "hr",
            "cs", "da", "nl", "en", "et", "fi", "fr", "gl", "de", "el",
            "he", "hi", "hu", "is", "id", "it", "ja", "kk", "ko", "lv",
            "lt", "mk", "ms", "mr", "mi", "ne", "no", "fa", "pl", "pt",
            "ro", "ru", "sr", "sk", "sl", "es", "sw", "sv", "tl", "ta",
            "th", "tr", "uk", "ur", "vi", "cy",
        ]

    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats.

        Returns:
            List[str]: List of format extensions
        """
        return [
            "mp3",
            "mp4",
            "mpeg",
            "mpga",
            "m4a",
            "wav",
            "webm",
        ]