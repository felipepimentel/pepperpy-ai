"""
ElevenLabs TTS Provider.

Implements text-to-speech capabilities using ElevenLabs API.
"""

import os
from typing import Any, AsyncIterator, Dict, List

import aiohttp

from ..base import TTSCapabilities, TTSProvider, TTSProviderError, TTSVoiceError


class ElevenLabsProvider(TTSProvider):
    """ElevenLabs TTS provider implementation."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, **kwargs):
        """Initialize the ElevenLabs provider.

        Args:
            **kwargs: Configuration options.

        Raises:
            TTSProviderError: If initialization fails.
        """
        self.api_key = os.environ.get("PEPPERPY_TTS_ELEVENLABS__API_KEY", "")
        if not self.api_key:
            raise TTSProviderError(
                "ElevenLabs API key not found. Set PEPPERPY_TTS_ELEVENLABS__API_KEY environment variable."
            )

        self.model_id = kwargs.get("model_id", "eleven_multilingual_v2")
        self.stability = kwargs.get("stability", 0.5)
        self.similarity_boost = kwargs.get("similarity_boost", 0.75)
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

    @property
    def capabilities(self) -> List[TTSCapabilities]:
        """Return the capabilities of this provider."""
        return [
            TTSCapabilities.TEXT_TO_SPEECH,
            TTSCapabilities.STREAMING,
            TTSCapabilities.VOICE_CLONING,
            TTSCapabilities.MULTILINGUAL,
        ]

    async def convert_text(self, text: str, voice_id: str, **kwargs) -> bytes:
        """Convert text to speech using ElevenLabs API.

        Args:
            text: The text to convert.
            voice_id: The voice ID to use.
            **kwargs: Additional parameters:
                - stability: Voice stability (0-1)
                - similarity_boost: Voice clarity and similarity boost (0-1)
                - model_id: Model ID to use

        Returns:
            Audio data as bytes.

        Raises:
            TTSProviderError: If the API request fails.
            TTSVoiceError: If the voice ID is invalid.
        """
        stability = kwargs.get("stability", self.stability)
        similarity_boost = kwargs.get("similarity_boost", self.similarity_boost)
        model_id = kwargs.get("model_id", self.model_id)

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }

        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=self.headers
                ) as response:
                    if response.status == 404:
                        raise TTSVoiceError(f"Voice ID '{voice_id}' not found")
                    if response.status != 200:
                        error_text = await response.text()
                        raise TTSProviderError(
                            f"ElevenLabs API returned status {response.status}: {error_text}"
                        )

                    return await response.read()
        except aiohttp.ClientError as e:
            raise TTSProviderError(
                f"Network error while communicating with ElevenLabs: {str(e)}"
            )
        except Exception as e:
            raise TTSProviderError(f"Error generating speech with ElevenLabs: {str(e)}")

    async def convert_text_stream(
        self, text: str, voice_id: str, **kwargs
    ) -> AsyncIterator[bytes]:
        """Stream audio from text using ElevenLabs API.

        Args:
            text: The text to convert.
            voice_id: The voice ID to use.
            **kwargs: Additional parameters:
                - stability: Voice stability (0-1)
                - similarity_boost: Voice clarity and similarity boost (0-1)
                - model_id: Model ID to use

        Yields:
            Audio chunks as bytes.

        Raises:
            TTSProviderError: If the API request fails.
            TTSVoiceError: If the voice ID is invalid.
        """
        stability = kwargs.get("stability", self.stability)
        similarity_boost = kwargs.get("similarity_boost", self.similarity_boost)
        model_id = kwargs.get("model_id", self.model_id)

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }

        url = f"{self.BASE_URL}/text-to-speech/{voice_id}/stream"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=self.headers
                ) as response:
                    if response.status == 404:
                        raise TTSVoiceError(f"Voice ID '{voice_id}' not found")
                    if response.status != 200:
                        error_text = await response.text()
                        raise TTSProviderError(
                            f"ElevenLabs API returned status {response.status}: {error_text}"
                        )

                    async for chunk in response.content.iter_chunked(1024):
                        yield chunk
        except aiohttp.ClientError as e:
            raise TTSProviderError(
                f"Network error while communicating with ElevenLabs: {str(e)}"
            )
        except Exception as e:
            raise TTSProviderError(f"Error streaming speech with ElevenLabs: {str(e)}")

    async def get_voices(self, **kwargs) -> List[Dict[str, Any]]:
        """Get available voices from ElevenLabs.

        Returns:
            List of voice information dictionaries.

        Raises:
            TTSProviderError: If the API request fails.
        """
        url = f"{self.BASE_URL}/voices"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise TTSProviderError(
                            f"ElevenLabs API returned status {response.status}: {error_text}"
                        )

                    data = await response.json()
                    # Convert to standardized format
                    return [
                        {
                            "id": voice["voice_id"],
                            "name": voice["name"],
                            "description": voice.get("description", ""),
                            "preview_url": voice.get("preview_url", ""),
                            "gender": voice.get("labels", {}).get("gender", "unknown"),
                            "age": voice.get("labels", {}).get("age", "unknown"),
                            "language": voice.get("labels", {}).get(
                                "language", "unknown"
                            ),
                            "provider_data": voice,
                        }
                        for voice in data.get("voices", [])
                    ]
        except aiohttp.ClientError as e:
            raise TTSProviderError(
                f"Network error while communicating with ElevenLabs: {str(e)}"
            )
        except Exception as e:
            raise TTSProviderError(f"Error fetching voices from ElevenLabs: {str(e)}")

    async def clone_voice(self, name: str, samples: List[bytes], **kwargs) -> str:
        """Clone a voice from audio samples using ElevenLabs.

        Args:
            name: Name for the cloned voice.
            samples: List of audio samples as bytes.
            **kwargs: Additional parameters.
                - description: Voice description
                - labels: Voice labels (dict)

        Returns:
            ID of the created voice.

        Raises:
            TTSProviderError: If the API request fails.
        """
        description = kwargs.get("description", "")
        labels = kwargs.get("labels", {})

        url = f"{self.BASE_URL}/voices/add"

        # Prepare form data
        data = aiohttp.FormData()
        data.add_field("name", name)
        data.add_field("description", description)

        if labels:
            data.add_field("labels", str(labels))

        # Add sample files
        for i, sample in enumerate(samples):
            data.add_field(
                "files", sample, filename=f"sample_{i}.mp3", content_type="audio/mpeg"
            )

        # Remove Content-Type from headers as it will be set by aiohttp
        headers = self.headers.copy()
        headers.pop("Content-Type", None)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise TTSProviderError(
                            f"ElevenLabs API returned status {response.status}: {error_text}"
                        )

                    data = await response.json()
                    return data.get("voice_id", "")
        except aiohttp.ClientError as e:
            raise TTSProviderError(
                f"Network error while communicating with ElevenLabs: {str(e)}"
            )
        except Exception as e:
            raise TTSProviderError(f"Error cloning voice with ElevenLabs: {str(e)}")
