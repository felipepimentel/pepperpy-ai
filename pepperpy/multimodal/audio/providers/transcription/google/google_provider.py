"""Google Cloud Speech-to-Text provider for transcription capability."""

from pathlib import Path
from typing import Dict, List, Optional, Union

from pepperpy.multimodal.audio.base import (
    TranscriptionError,
    TranscriptionProvider,
)


class GoogleTranscriptionProvider(TranscriptionProvider):
    """Provider implementation for Google Cloud Speech-to-Text capabilities."""

    def __init__(
        self,
        credentials: Optional[Dict[str, str]] = None,
        project_id: Optional[str] = None,
        **kwargs,
    ):
        """Initialize Google Cloud Speech-to-Text provider.

        Args:
            credentials: Google Cloud credentials
            project_id: Google Cloud project ID
            **kwargs: Additional configuration parameters
        
        Raises:
            ImportError: If google-cloud-speech package is not installed
            TranscriptionError: If initialization fails

        """
        try:
            # Import Google Cloud Speech
            from google.cloud import speech
        except ImportError:
            raise ImportError(
                "google-cloud-speech package is required for GoogleTranscriptionProvider. "
                "Install it with: pip install google-cloud-speech",
            ) from None

        self.kwargs = kwargs
        self.credentials = credentials
        self.project_id = project_id

        try:
            # Initialize client
            self.client = speech.SpeechClient()
        except Exception as e:
            raise TranscriptionError(f"Failed to initialize Google Cloud client: {e}") from e

    def transcribe(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> List[Dict]:
        """Transcribe audio to text.

        Args:
            audio: Audio data as file path or bytes
            language: Language code (e.g., 'en-US')
            **kwargs: Additional parameters

        Returns:
            List of transcription segments

        Raises:
            TranscriptionError: If transcription fails

        """
        try:
            from google.cloud import speech

            # Handle audio input
            audio_content = None
            if isinstance(audio, (str, Path)):
                with open(audio, "rb") as f:
                    audio_content = f.read()
            elif isinstance(audio, bytes):
                audio_content = audio
            else:
                raise ValueError(f"Unsupported audio type: {type(audio)}")

            # Create audio object
            audio_obj = speech.RecognitionAudio(content=audio_content)

            # Prepare config
            config = speech.RecognitionConfig(
                language_code=language or "en-US",
                **self.kwargs,
                **kwargs,
            )

            # Transcribe audio
            response = self.client.recognize(config=config, audio=audio_obj)

            # Process results
            segments = []
            for result in response.results:
                for alternative in result.alternatives:
                    segment = {
                        "text": alternative.transcript,
                        "confidence": alternative.confidence,
                        "start": 0.0,  # Basic recognize doesn't provide timestamps
                        "end": 0.0,
                    }
                    segments.append(segment)

            return segments

        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio: {e}") from e

    def transcribe_with_timestamps(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> List[Dict]:
        """Transcribe audio with word-level timestamps.

        Args:
            audio: Audio data as file path or bytes
            language: Language code (e.g., 'en-US')
            **kwargs: Additional parameters

        Returns:
            List of transcription segments with timestamps

        Raises:
            TranscriptionError: If transcription fails

        """
        try:
            from google.cloud import speech

            # Handle audio input
            audio_content = None
            if isinstance(audio, (str, Path)):
                with open(audio, "rb") as f:
                    audio_content = f.read()
            elif isinstance(audio, bytes):
                audio_content = audio
            else:
                raise ValueError(f"Unsupported audio type: {type(audio)}")

            # Create audio object
            audio_obj = speech.RecognitionAudio(content=audio_content)

            # Prepare config with word time offsets
            config = speech.RecognitionConfig(
                language_code=language or "en-US",
                enable_word_time_offsets=True,
                **self.kwargs,
                **kwargs,
            )

            # Transcribe audio
            response = self.client.recognize(config=config, audio=audio_obj)

            # Process results with timestamps
            segments = []
            for result in response.results:
                for alternative in result.alternatives:
                    words = []
                    for word_info in alternative.words:
                        word_data = {
                            "word": word_info.word,
                            "start": word_info.start_time.total_seconds(),
                            "end": word_info.end_time.total_seconds(),
                        }
                        words.append(word_data)

                    # Create segment from words
                    if words:
                        segment = {
                            "text": alternative.transcript,
                            "confidence": alternative.confidence,
                            "start": words[0]["start"],
                            "end": words[-1]["end"],
                            "words": words,
                        }
                        segments.append(segment)

            return segments

        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio: {e}") from e

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes.

        Returns:
            List of supported language codes

        """
        # Google Cloud Speech supports many languages
        # This is a subset of commonly used ones
        return [
            "en-US",  # English (United States)
            "en-GB",  # English (United Kingdom)
            "es-ES",  # Spanish (Spain)
            "es-US",  # Spanish (United States)
            "fr-FR",  # French
            "de-DE",  # German
            "it-IT",  # Italian
            "pt-BR",  # Portuguese (Brazil)
            "ru-RU",  # Russian
            "ja-JP",  # Japanese
            "ko-KR",  # Korean
            "zh-CN",  # Chinese (Simplified)
            "zh-TW",  # Chinese (Traditional)
            "ar-SA",  # Arabic
            "hi-IN",  # Hindi
        ]

    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats.

        Returns:
            List of supported audio format extensions

        """
        return [
            "wav",
            "mp3",
            "flac",
            "ogg",
            "m4a",
            "aac",
            "amr",
            "amr-wb",
        ]
