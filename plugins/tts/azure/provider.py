"""Azure TTS provider for PepperPy."""

from typing import Any, AsyncGenerator, AsyncIterator, Dict, List

from pepperpy.core.base import ValidationError
from pepperpy.tts.base import TTSProvider

try:
    import azure.cognitiveservices.speech as speechsdk

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class AzureProvider(TTSProvider):
    """Azure TTS provider implementation."""

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
def __init__(
        self,
        subscription_key: str,
        region: str,
        voice_name: str = "en-US-JennyNeural",
        **kwargs: Any,
    ) -> None:
        """Initialize Azure TTS provider.

        Args:
            subscription_key: Azure subscription key
            region: Azure region
            voice_name: Voice name to use
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.subscription_key = subscription_key
        self.region = region
        self.voice_name = voice_name
        self.speech_config = None
        self.speech_synthesizer = None

    async def initialize(self) -> None:
        """Initialize the TTS provider.

        Raises:
            ValidationError if azure-cognitiveservices-speech package not installed
        """
        if not AZURE_AVAILABLE:
            raise ValidationError(
                "azure-cognitiveservices-speech package not installed. "
                "Install it with: pip install azure-cognitiveservices-speech"
            )

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.subscription_key, region=self.region
        )
        self.speech_config.speech_synthesis_voice_name = self.voice_name
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config
        )

    async def convert_text(self, text: str) -> bytes:
        """Convert text to speech.

        Args:
            text: Text to convert

        Returns:
            Audio data as bytes

        Raises:
            ValidationError if conversion fails
        """
        if not self.speech_synthesizer:
            raise ValidationError("Provider not initialized")

        result = self.speech_synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        else:
            raise ValidationError(
                f"Speech synthesis failed: {result.reason} {result.error_details}"
            )

    async def stream_text(self, text: str) -> AsyncIterator[bytes]:
        """Stream text to speech.

        Args:
            text: Text to convert

        Yields:
            Audio data chunks

        Raises:
            ValidationError if streaming fails
        """
        if not self.speech_synthesizer:
            raise ValidationError("Provider not initialized")

        result = self.speech_synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Split audio into chunks
            chunk_size = 1024 * 16  # 16KB chunks
            audio_data = result.audio_data
            for i in range(0, len(audio_data), chunk_size):
                yield audio_data[i : i + chunk_size]
        else:
            raise ValidationError(
                f"Speech synthesis failed: {result.reason} {result.error_details}"
            )

    async def get_voices(self) -> List[Dict[str, Any]]:
        """Get available voices.

        Returns:
            List of voice information dictionaries

        Raises:
            ValidationError if provider not initialized
        """
        if not self.speech_synthesizer:
            raise ValidationError("Provider not initialized")

        voices = []
        result = self.speech_synthesizer.get_voices_async().get()
        if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
            for voice in result.voices:
                voices.append({
                    "name": voice.name,
                    "locale": voice.locale,
                    "gender": voice.gender,
                    "style_list": voice.style_list,
                })
            return voices
        else:
            raise ValidationError(
                f"Failed to get voices: {result.reason} {result.error_details}"
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.speech_config = None
        self.speech_synthesizer = None

    async def synthesize(
        self,
        text: str,
        voice: str = "en-US-JennyNeural",
        output_format: str = "audio-16khz-32kbitrate-mono-mp3",
        **kwargs: Any,
    ) -> bytes:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize
            voice: Voice to use
            output_format: Output audio format
            **kwargs: Additional synthesis options

        Returns:
            Audio data as bytes

        Raises:
            ValidationError if synthesis fails
        """
        if not self.speech_synthesizer or not self.speech_config:
            raise ValidationError("Provider not initialized")

        try:
            # Configure synthesis
            self.speech_config.set_speech_synthesis_output_format(
                getattr(
                    speechsdk.SpeechSynthesisOutputFormat,
                    output_format.replace("-", "_"),
                )
            )
            self.speech_config.speech_synthesis_voice_name = voice

            # Synthesize text
            result = self.speech_synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            else:
                raise ValidationError(
                    f"Speech synthesis failed: {result.reason} {result.error_details}"
                )
        except Exception as e:
            raise ValidationError(f"Speech synthesis failed: {str(e)}") from e

    async def convert_text_stream(
        self, text: str, voice_id: str, **kwargs: Any
    ) -> AsyncGenerator[bytes, None]:
        """Convert text to speech and stream the audio data."""
        try:
            # Split audio into chunks
            chunk_size = 1024 * 16  # 16KB chunks
            audio_data = await self.convert_text(text)
            for i in range(0, len(audio_data), chunk_size):
                yield audio_data[i : i + chunk_size]
        except Exception as e:
            raise ValidationError(f"Text streaming failed: {str(e)}") from e

    async def clone_voice(self, name: str, samples: List[bytes], **kwargs: Any) -> str:
        """Clone a voice from audio samples.

        Args:
            name: Name for the cloned voice
            samples: List of audio samples
            **kwargs: Additional provider-specific parameters

        Returns:
            ID of the cloned voice

        Raises:
            ValidationError if cloning fails
        """
        raise ValidationError("Voice cloning not supported by Azure TTS")
