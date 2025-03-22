"""
Play.ht TTS Provider.

Implements text-to-speech capabilities using Play.ht API.
"""

import asyncio
import os
import time
from typing import Any, AsyncIterator, Dict, List

import aiohttp

from ..base import TTSCapabilities, TTSProvider, TTSProviderError, TTSVoiceError


class PlayHTProvider(TTSProvider):
    """Play.ht TTS provider implementation."""

    BASE_URL = "https://api.play.ht/api/v2"

    def __init__(self, **kwargs):
        """Initialize the Play.ht provider.

        Args:
            **kwargs: Configuration options.

        Raises:
            TTSProviderError: If initialization fails.
        """
        self.api_key = os.environ.get("PEPPERPY_TTS_PLAYHT__API_KEY", "")
        self.user_id = os.environ.get("PEPPERPY_TTS_PLAYHT__USER_ID", "")

        if not self.api_key:
            raise TTSProviderError(
                "Play.ht API key not found. Set PEPPERPY_TTS_PLAYHT__API_KEY environment variable."
            )
        if not self.user_id:
            raise TTSProviderError(
                "Play.ht User ID not found. Set PEPPERPY_TTS_PLAYHT__USER_ID environment variable."
            )

        self.voice_engine = kwargs.get("voice_engine", "PlayHT2.0-turbo")
        self.quality = kwargs.get("quality", "premium")
        self.speed = kwargs.get("speed", 1.0)
        self.headers = {
            "AUTHORIZATION": self.api_key,
            "X-USER-ID": self.user_id,
            "Content-Type": "application/json",
        }

    @property
    def capabilities(self) -> List[TTSCapabilities]:
        """Return the capabilities of this provider."""
        return [
            TTSCapabilities.TEXT_TO_SPEECH,
            TTSCapabilities.STREAMING,
            TTSCapabilities.VOICE_CLONING,
            TTSCapabilities.MULTILINGUAL,
            TTSCapabilities.EMOTION_CONTROL,
        ]

    async def _create_speech_job(self, text: str, voice_id: str, **kwargs) -> str:
        """Create a speech generation job.

        Args:
            text: The text to convert.
            voice_id: The voice ID to use.
            **kwargs: Additional parameters.

        Returns:
            Speech job ID.

        Raises:
            TTSProviderError: If the API request fails.
        """
        voice_engine = kwargs.get("voice_engine", self.voice_engine)
        quality = kwargs.get("quality", self.quality)
        speed = kwargs.get("speed", self.speed)

        payload = {
            "text": text,
            "voice": voice_id,
            "quality": quality,
            "output_format": "mp3",
            "speed": speed,
            "sample_rate": 24000,
            "voice_engine": voice_engine,
        }

        # Add emotion parameters if provided
        emotion = kwargs.get("emotion")
        if emotion:
            payload["emotion"] = emotion

        url = f"{self.BASE_URL}/tts"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=self.headers
                ) as response:
                    if response.status == 404:
                        raise TTSVoiceError(f"Voice ID '{voice_id}' not found")
                    if response.status != 201:
                        error_text = await response.text()
                        raise TTSProviderError(
                            f"Play.ht API returned status {response.status}: {error_text}"
                        )

                    data = await response.json()
                    return data.get("id", "")
        except aiohttp.ClientError as e:
            raise TTSProviderError(
                f"Network error while communicating with Play.ht: {str(e)}"
            )
        except Exception as e:
            raise TTSProviderError(f"Error creating speech job with Play.ht: {str(e)}")

    async def _wait_for_job_completion(
        self, job_id: str, max_wait_seconds: int = 60
    ) -> Dict[str, Any]:
        """Wait for a speech job to complete.

        Args:
            job_id: The job ID to wait for.
            max_wait_seconds: Maximum time to wait in seconds.

        Returns:
            Job details including audio URL.

        Raises:
            TTSProviderError: If waiting for the job fails.
        """
        url = f"{self.BASE_URL}/tts/{job_id}"

        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=self.headers) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise TTSProviderError(
                                f"Play.ht API returned status {response.status}: {error_text}"
                            )

                        data = await response.json()
                        status = data.get("status")

                        if status == "COMPLETED":
                            return data
                        elif status in ["FAILED", "ERROR"]:
                            error_message = data.get("error", "Unknown error")
                            raise TTSProviderError(
                                f"Play.ht job failed: {error_message}"
                            )

                        # Wait before checking again
                        await asyncio.sleep(2)
            except aiohttp.ClientError as e:
                raise TTSProviderError(
                    f"Network error while checking job status: {str(e)}"
                )
            except TTSProviderError:
                raise
            except Exception as e:
                raise TTSProviderError(f"Error checking job status: {str(e)}")

        raise TTSProviderError(
            f"Timeout waiting for Play.ht job completion after {max_wait_seconds} seconds"
        )

    async def _download_audio(self, url: str) -> bytes:
        """Download audio from URL.

        Args:
            url: URL to download from.

        Returns:
            Audio data as bytes.

        Raises:
            TTSProviderError: If downloading fails.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise TTSProviderError(
                            f"Error downloading audio, status {response.status}: {error_text}"
                        )

                    return await response.read()
        except aiohttp.ClientError as e:
            raise TTSProviderError(f"Network error while downloading audio: {str(e)}")
        except Exception as e:
            raise TTSProviderError(f"Error downloading audio: {str(e)}")

    async def convert_text(self, text: str, voice_id: str, **kwargs) -> bytes:
        """Convert text to speech using Play.ht API.

        Args:
            text: The text to convert.
            voice_id: The voice ID to use.
            **kwargs: Additional parameters:
                - voice_engine: Voice engine to use
                - quality: Audio quality ('standard' or 'premium')
                - speed: Playback speed (0.5-2.0)
                - emotion: Emotion to apply (happy, sad, etc.)

        Returns:
            Audio data as bytes.

        Raises:
            TTSProviderError: If the API request fails.
            TTSVoiceError: If the voice ID is invalid.
        """
        # Create speech job
        job_id = await self._create_speech_job(text, voice_id, **kwargs)

        # Wait for job completion
        job_details = await self._wait_for_job_completion(job_id)

        # Download the audio
        url = job_details.get("url")
        if not url:
            raise TTSProviderError("No audio URL found in completed job")

        return await self._download_audio(url)

    async def convert_text_stream(
        self, text: str, voice_id: str, **kwargs
    ) -> AsyncIterator[bytes]:
        """Stream audio from text using Play.ht API.

        Note: Play.ht doesn't support true streaming, so this fetches the
        complete audio and yields it in chunks.

        Args:
            text: The text to convert.
            voice_id: The voice ID to use.
            **kwargs: Additional parameters:
                - voice_engine: Voice engine to use
                - quality: Audio quality ('standard' or 'premium')
                - speed: Playback speed (0.5-2.0)
                - emotion: Emotion to apply (happy, sad, etc.)

        Yields:
            Audio chunks as bytes.

        Raises:
            TTSProviderError: If the API request fails.
            TTSVoiceError: If the voice ID is invalid.
        """
        audio_data = await self.convert_text(text, voice_id, **kwargs)

        # Yield in chunks
        chunk_size = 1024
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i : i + chunk_size]

    async def get_voices(self, **kwargs) -> List[Dict[str, Any]]:
        """Get available voices from Play.ht.

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
                            f"Play.ht API returned status {response.status}: {error_text}"
                        )

                    data = await response.json()

                    # Convert to standardized format
                    voices = []
                    for voice in data:
                        language = voice.get("language", "")
                        language_code = (
                            language.split("-")[0] if language else "unknown"
                        )

                        voices.append(
                            {
                                "id": voice.get("id", ""),
                                "name": voice.get("name", ""),
                                "description": voice.get("description", ""),
                                "preview_url": voice.get("sample", ""),
                                "gender": voice.get("gender", "unknown"),
                                "age": "unknown",  # Play.ht doesn't provide age
                                "language": language_code,
                                "provider_data": voice,
                            }
                        )

                    return voices
        except aiohttp.ClientError as e:
            raise TTSProviderError(
                f"Network error while communicating with Play.ht: {str(e)}"
            )
        except Exception as e:
            raise TTSProviderError(f"Error fetching voices from Play.ht: {str(e)}")

    async def clone_voice(self, name: str, samples: List[bytes], **kwargs) -> str:
        """Clone a voice from audio samples using Play.ht.

        Args:
            name: Name for the cloned voice.
            samples: List of audio samples as bytes.
            **kwargs: Additional parameters:
                - description: Voice description

        Returns:
            ID of the created voice.

        Raises:
            TTSProviderError: If the API request fails.
        """
        description = kwargs.get("description", "")

        url = f"{self.BASE_URL}/voice-cloning"

        # Prepare form data
        data = aiohttp.FormData()
        data.add_field("name", name)
        data.add_field("description", description)

        # Add sample files
        for i, sample in enumerate(samples):
            data.add_field(
                "samples", sample, filename=f"sample_{i}.mp3", content_type="audio/mpeg"
            )

        # Remove Content-Type from headers as it will be set by aiohttp
        headers = self.headers.copy()
        headers.pop("Content-Type", None)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise TTSProviderError(
                            f"Play.ht API returned status {response.status}: {error_text}"
                        )

                    data = await response.json()
                    return data.get("id", "")
        except aiohttp.ClientError as e:
            raise TTSProviderError(
                f"Network error while communicating with Play.ht: {str(e)}"
            )
        except Exception as e:
            raise TTSProviderError(f"Error cloning voice with Play.ht: {str(e)}")
