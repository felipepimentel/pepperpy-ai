"""
Murf.ai TTS provider implementation.
"""

import asyncio
import os
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp
from murf import Murf

from ..base import TTSProviderError, TTSVoiceError


class MurfProvider:
    """Provider for Murf.ai TTS service."""

    BASE_URL = "https://api.murf.ai/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Murf.ai provider.

        Args:
            api_key: The API key for Murf.ai. If not provided, will try to get from environment.
        """
        env_key = os.environ.get("PEPPERPY_TTS_MURF__API_KEY")
        if not api_key and not env_key:
            raise TTSProviderError("No API key provided for Murf.ai")

        # Initialize the Murf client
        self.client = Murf(api_key=api_key or env_key)

        # Initialize headers for API requests
        self.headers = {
            "Authorization": f"Bearer {api_key or env_key}",
            "Content-Type": "application/json",
        }

    @property
    def capabilities(self) -> List[str]:
        """Return the capabilities of this provider."""
        return [
            "text_to_speech",
            "multilingual",
        ]

    async def _create_tts_job(
        self, text: str, voice_id: str, **kwargs
    ) -> Dict[str, Any]:
        """Create a text-to-speech job in Murf.ai.

        Args:
            text: The text to convert.
            voice_id: The voice ID to use.
            **kwargs: Additional parameters.

        Returns:
            Job details including job ID.

        Raises:
            TTSProviderError: If the API request fails.
        """
        rate = kwargs.get("rate", 0)  # Default rate (0 = normal)
        pitch = kwargs.get("pitch", 0)  # Default pitch (0 = normal)
        format_type = kwargs.get("format", "mp3")

        payload = {
            "text": text,
            "voiceId": voice_id,
            "rate": rate,
            "pitch": pitch,
            "format": format_type,
        }

        url = f"{self.BASE_URL}/speech/generate"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=self.headers
                ) as response:
                    if response.status == 404:
                        raise TTSVoiceError(f"Voice ID '{voice_id}' not found")

                    response_data = await response.json()

                    if response.status != 200:
                        error_message = response_data.get("message", "Unknown error")
                        raise TTSProviderError(f"Murf.ai API error: {error_message}")

                    return response_data
        except aiohttp.ClientError as e:
            raise TTSProviderError(
                f"Network error while communicating with Murf.ai: {str(e)}"
            ) from e
        except Exception as e:
            if isinstance(e, TTSProviderError):
                raise
            raise TTSProviderError(
                f"Error generating speech with Murf.ai: {str(e)}"
            ) from e

    async def _get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a text-to-speech job.

        Args:
            job_id: The job ID to check.

        Returns:
            Job details including status and audio URL if complete.

        Raises:
            TTSProviderError: If the API request fails.
        """
        url = f"{self.BASE_URL}/jobs/{job_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise TTSProviderError(
                            f"Murf.ai API returned status {response.status}: {error_text}"
                        )

                    return await response.json()
        except aiohttp.ClientError as e:
            raise TTSProviderError(
                f"Network error while checking job status: {str(e)}"
            ) from e
        except Exception as e:
            raise TTSProviderError(f"Error checking job status: {str(e)}") from e

    async def _wait_for_job_completion(
        self, job_id: str, max_wait_seconds: int = 60
    ) -> Dict[str, Any]:
        """Wait for a text-to-speech job to complete.

        Args:
            job_id: The job ID to wait for.
            max_wait_seconds: Maximum time to wait in seconds.

        Returns:
            Job details including audio URL.

        Raises:
            TTSProviderError: If waiting for the job fails.
        """
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            job_status = await self._get_job_status(job_id)

            status = job_status.get("status")
            if status == "completed":
                return job_status
            elif status == "failed":
                error_message = job_status.get("error", "Unknown error")
                raise TTSProviderError(f"Murf.ai job failed: {error_message}")

            # Wait before checking again
            await asyncio.sleep(2)

        raise TTSProviderError(
            f"Timeout waiting for Murf.ai job completion after {max_wait_seconds} seconds"
        )

    async def _download_audio(self, audio_url: str) -> bytes:
        """Download audio from URL.

        Args:
            audio_url: URL to download audio from.

        Returns:
            Audio data as bytes.

        Raises:
            TTSProviderError: If downloading fails.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url, headers=self.headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise TTSProviderError(f"Error downloading audio: {error_text}")

                    return await response.read()
        except aiohttp.ClientError as e:
            raise TTSProviderError(
                f"Network error while downloading audio: {str(e)}"
            ) from e
        except Exception as e:
            raise TTSProviderError(f"Error downloading audio: {str(e)}") from e

    async def get_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices from Murf.ai API."""
        try:
            # Get voices using the Murf SDK
            voices = self.client.text_to_speech.get_voices()
            return [
                {
                    "id": voice.voice_id,
                    "name": voice.display_name,
                    "description": voice.description,
                    "preview_url": None,
                    "gender": voice.gender,
                    "age": None,
                    "language": voice.locale,
                    "provider_data": {"accent": voice.accent},
                }
                for voice in voices
            ]
        except Exception as e:
            raise TTSProviderError(f"Error fetching voices: {str(e)}") from e

    async def convert_text(self, text: str, voice_id: str, **kwargs) -> bytes:
        """Convert text to speech using Murf.ai API."""
        try:
            # Generate audio using the Murf SDK
            response = self.client.text_to_speech.generate(
                text=text,
                voice_id=voice_id,  # Murf.ai expects the exact voice ID
                rate=kwargs.get("rate", 0),  # Default rate (0 = normal)
                pitch=kwargs.get("pitch", 0),  # Default pitch (0 = normal)
                format="MP3",  # Murf.ai requires uppercase format
            )

            # Download the audio file
            if not response.audio_file:
                raise TTSProviderError("No audio file URL returned from Murf.ai")

            async with aiohttp.ClientSession() as session:
                async with session.get(response.audio_file) as audio_response:
                    if audio_response.status == 200:
                        return await audio_response.read()
                    else:
                        error_data = await audio_response.text()
                        raise TTSProviderError(f"Error downloading audio: {error_data}")
        except Exception as e:
            raise TTSProviderError(f"Error generating speech: {str(e)}") from e

    async def convert_text_stream(
        self, text: str, voice_id: str, chunk_size: int = 1024, **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """Convert text to speech and stream the audio data."""
        audio_data = await self.convert_text(text, voice_id, **kwargs)
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i : i + chunk_size]

    async def clone_voice(self, name: str, samples: List[bytes], **kwargs) -> str:
        """Clone a voice from audio samples.

        Not supported by Murf.ai API yet.
        """
        raise NotImplementedError("Voice cloning is not supported by Murf.ai API")
