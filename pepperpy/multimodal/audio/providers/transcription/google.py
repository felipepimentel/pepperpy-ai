"""Provider implementation for Google Cloud Speech-to-Text capabilities."""

from pathlib import Path
from typing import Dict, List, Optional, Union

from pepperpy.providers.audio.transcription.base import (
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
            credentials: Optional service account credentials
            project_id: Optional Google Cloud project ID
            **kwargs: Additional parameters to pass to Google Cloud

        Raises:
            ImportError: If google-cloud-speech package is not installed
            TranscriptionError: If initialization fails
        """
        try:
            from google.cloud import speech
        except ImportError:
            raise ImportError(
                "google-cloud-speech package is required for GoogleTranscriptionProvider. "
                "Install it with: pip install google-cloud-speech"
            )

        self.kwargs = kwargs

        try:
            self.client = speech.SpeechClient(
                credentials=credentials,
                project=project_id,
            )
        except Exception as e:
            raise TranscriptionError(f"Failed to initialize Google Cloud client: {e}")

    def transcribe(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Transcribe audio using Google Cloud Speech-to-Text.

        Args:
            audio: Path to audio file, audio file bytes, or URL
            language: Optional language code (e.g. 'en-US', 'pt-BR')
            **kwargs: Additional parameters to pass to Google Cloud

        Returns:
            str: Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            from google.cloud import speech

            # Handle different audio input types
            if isinstance(audio, (str, Path)):
                audio_path = Path(audio)
                if not audio_path.exists():
                    raise TranscriptionError(f"Audio file not found: {audio_path}")
                with open(audio_path, "rb") as f:
                    content = f.read()
            else:
                content = audio

            # Prepare audio input
            audio_input = speech.RecognitionAudio(content=content)

            # Prepare config
            config = speech.RecognitionConfig(
                language_code=language or "en-US",
                **self.kwargs,
                **kwargs,
            )

            # Transcribe audio
            response = self.client.recognize(
                config=config,
                audio=audio_input,
            )

            # Combine all transcripts
            text = " ".join(
                result.alternatives[0].transcript
                for result in response.results
                if result.alternatives
            )

            return text

        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio: {e}")

    def transcribe_with_timestamps(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Union[str, float]]]:
        """Transcribe audio with timestamps using Google Cloud Speech-to-Text.

        Args:
            audio: Path to audio file, audio file bytes, or URL
            language: Optional language code (e.g. 'en-US', 'pt-BR')
            **kwargs: Additional parameters to pass to Google Cloud

        Returns:
            List[Dict[str, Union[str, float]]]: List of segments with text and timestamps

        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            from google.cloud import speech

            # Handle different audio input types
            if isinstance(audio, (str, Path)):
                audio_path = Path(audio)
                if not audio_path.exists():
                    raise TranscriptionError(f"Audio file not found: {audio_path}")
                with open(audio_path, "rb") as f:
                    content = f.read()
            else:
                content = audio

            # Prepare audio input
            audio_input = speech.RecognitionAudio(content=content)

            # Prepare config with word time offsets
            config = speech.RecognitionConfig(
                language_code=language or "en-US",
                enable_word_time_offsets=True,
                **self.kwargs,
                **kwargs,
            )

            # Transcribe audio
            response = self.client.recognize(
                config=config,
                audio=audio_input,
            )

            # Extract segments with timestamps
            segments = []
            for result in response.results:
                if result.alternatives:
                    words = result.alternatives[0].words
                    if words:
                        current_segment = {
                            "text": "",
                            "start": words[0].start_time.total_seconds(),
                            "end": words[-1].end_time.total_seconds(),
                        }
                        for word in words:
                            current_segment["text"] += f" {word.word}"
                        current_segment["text"] = current_segment["text"].strip()
                        segments.append(current_segment)

            return segments

        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio: {e}")

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes.

        Returns:
            List[str]: List of language codes
        """
        return [
            "af-ZA",
            "am-ET",
            "ar-AE",
            "ar-BH",
            "ar-DZ",
            "ar-EG",
            "ar-IL",
            "ar-IQ",
            "ar-JO",
            "ar-KW",
            "ar-LB",
            "ar-MA",
            "ar-OM",
            "ar-PS",
            "ar-QA",
            "ar-SA",
            "ar-TN",
            "ar-YE",
            "az-AZ",
            "bg-BG",
            "bn-BD",
            "bn-IN",
            "bs-BA",
            "ca-ES",
            "cs-CZ",
            "da-DK",
            "de-AT",
            "de-CH",
            "de-DE",
            "el-GR",
            "en-AU",
            "en-CA",
            "en-GB",
            "en-GH",
            "en-HK",
            "en-IE",
            "en-IN",
            "en-KE",
            "en-NG",
            "en-NZ",
            "en-PH",
            "en-PK",
            "en-SG",
            "en-TZ",
            "en-US",
            "en-ZA",
            "es-AR",
            "es-BO",
            "es-CL",
            "es-CO",
            "es-CR",
            "es-DO",
            "es-EC",
            "es-ES",
            "es-GT",
            "es-HN",
            "es-MX",
            "es-NI",
            "es-PA",
            "es-PE",
            "es-PR",
            "es-PY",
            "es-SV",
            "es-US",
            "es-UY",
            "es-VE",
            "et-EE",
            "eu-ES",
            "fa-IR",
            "fi-FI",
            "fil-PH",
            "fr-BE",
            "fr-CA",
            "fr-CH",
            "fr-FR",
            "gl-ES",
            "gu-IN",
            "he-IL",
            "hi-IN",
            "hr-HR",
            "hu-HU",
            "hy-AM",
            "id-ID",
            "is-IS",
            "it-CH",
            "it-IT",
            "ja-JP",
            "jv-ID",
            "ka-GE",
            "kk-KZ",
            "km-KH",
            "kn-IN",
            "ko-KR",
            "lo-LA",
            "lt-LT",
            "lv-LV",
            "mk-MK",
            "ml-IN",
            "mn-MN",
            "mr-IN",
            "ms-MY",
            "mt-MT",
            "my-MM",
            "nb-NO",
            "ne-NP",
            "nl-BE",
            "nl-NL",
            "pa-Guru-IN",
            "pl-PL",
            "ps-AF",
            "pt-BR",
            "pt-PT",
            "ro-RO",
            "ru-RU",
            "si-LK",
            "sk-SK",
            "sl-SI",
            "sq-AL",
            "sr-RS",
            "su-ID",
            "sv-SE",
            "sw-KE",
            "sw-TZ",
            "ta-IN",
            "ta-LK",
            "ta-MY",
            "ta-SG",
            "te-IN",
            "th-TH",
            "tr-TR",
            "uk-UA",
            "ur-IN",
            "ur-PK",
            "uz-UZ",
            "vi-VN",
            "zu-ZA",
        ]

    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats.

        Returns:
            List[str]: List of format extensions
        """
        return [
            "flac",
            "wav",
            "mp3",
            "ogg",
            "webm",
            "amr",
            "amr-wb",
        ]
