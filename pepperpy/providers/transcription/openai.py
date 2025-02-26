"""OpenAI transcription provider implementation."""

from pathlib import Path
from typing import Dict, List, Optional, Union

from pepperpy.providers.transcription.base import TranscriptionError, TranscriptionProvider


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
            model: Model to use for transcription
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

    def _load_audio(self, audio: Union[str, Path, bytes]) -> Union[str, bytes]:
        """Load audio data.

        Args:
            audio: Path to audio file, audio file bytes, or URL

        Returns:
            Union[str, bytes]: Audio data or URL

        Raises:
            TranscriptionError: If audio loading fails
        """
        try:
            if isinstance(audio, (str, Path)):
                path = Path(audio)
                if path.exists():
                    with open(path, "rb") as f:
                        return f.read()
                return str(audio)  # Treat as URL
            return audio
        except Exception as e:
            raise TranscriptionError(f"Failed to load audio: {e}")

    def transcribe(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Transcribe audio to text.

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
            # Load audio data
            audio_data = self._load_audio(audio)

            # Prepare parameters
            params = {
                "model": self.model,
                "language": language,
                **self.kwargs,
                **kwargs,
            }

            # Call OpenAI API
            if isinstance(audio_data, str):
                response = self.client.audio.transcriptions.create(
                    file=audio_data,
                    **params,
                )
            else:
                response = self.client.audio.transcriptions.create(
                    file=("audio", audio_data),
                    **params,
                )

            return response.text

        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio: {e}")

    def transcribe_with_timestamps(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Union[str, float]]]:
        """Transcribe audio to text with word/segment timestamps.

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
            # Load audio data
            audio_data = self._load_audio(audio)

            # Prepare parameters
            params = {
                "model": self.model,
                "language": language,
                "response_format": "verbose_json",
                **self.kwargs,
                **kwargs,
            }

            # Call OpenAI API
            if isinstance(audio_data, str):
                response = self.client.audio.transcriptions.create(
                    file=audio_data,
                    **params,
                )
            else:
                response = self.client.audio.transcriptions.create(
                    file=("audio", audio_data),
                    **params,
                )

            # Extract segments with timestamps
            segments = []
            for segment in response.segments:
                segments.append({
                    "text": segment.text,
                    "start": segment.start,
                    "end": segment.end,
                    "confidence": segment.confidence,
                })
            return segments

        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio with timestamps: {e}")

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes.

        Returns:
            List[str]: List of language codes
        """
        # List of languages supported by Whisper
        # Source: https://platform.openai.com/docs/guides/speech-to-text/supported-languages
        return [
            "af", "ar", "hy", "az", "be", "bs", "bg", "ca", "zh", "hr",
            "cs", "da", "nl", "en", "et", "fi", "fr", "gl", "de", "el",
            "he", "hi", "hu", "is", "id", "it", "ja", "kn", "kk", "ko",
            "lv", "lt", "mk", "ms", "ml", "mt", "mr", "ne", "no", "fa",
            "pl", "pt", "ro", "ru", "sr", "sk", "sl", "es", "sw", "sv",
            "tl", "ta", "th", "tr", "uk", "ur", "vi", "cy",
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