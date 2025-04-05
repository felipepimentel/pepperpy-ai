"""Murf TTS provider for PepperPy."""

import asyncio
from typing import Any, List, Optional

import aiohttp
from murf import Murf

from pepperpy.core.errors import ProviderError
from pepperpy.plugin import ProviderPlugin
from pepperpy.tts.base import TTSAudio, TTSProvider, TTSProviderError, TTSVoice


class MurfTTSProvider(ProviderPlugin, TTSProvider):
    """Murf TTS provider implementation."""

    BASE_URL = "https://api.murf.ai/v1"

    def __init__(self):
        """Initialize the provider."""
        super().__init__()
        self._session: Optional[aiohttp.ClientSession] = None
        self._api_key = self._config.get("api_key")
        if not self._api_key:
            raise TTSProviderError("API key not found in configuration")
        self._logger.info("Initialized Murf TTS provider")
        self._client = None

    async def initialize(self) -> None:
        """Initialize provider resources."""
        if self.initialized:
            return

        # Initialize HTTP session
        self._session = aiohttp.ClientSession(
            base_url=self.BASE_URL, headers={"Authorization": f"Bearer {self._api_key}"}
        )

        # Initialize Murf client
        self._client = Murf(api_key=self._api_key)

        self._logger.debug("Murf TTS provider initialized")

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._session:
            await self._session.close()
            self._session = None
        self._client = None

    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs: Any,
    ) -> TTSAudio:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize
            voice_id: Voice ID to use
            output_path: Optional path to save audio
            **kwargs: Additional synthesis options

        Returns:
            TTSAudio object

        Raises:
            ProviderError: If synthesis fails
        """
        if not text:
            raise ValueError("Text cannot be empty")

        try:
            # Create TTS job
            job_id = await self._create_tts_job(
                text=text,
                voice_id=voice_id or self._config.get("voice_id", "en-US-1"),
                rate=kwargs.get("rate", self._config.get("rate", 100)),
                pitch=kwargs.get("pitch", self._config.get("pitch", 100)),
                format=kwargs.get("format", self._config.get("format", "wav")),
            )

            # Wait for job completion
            await self._wait_for_job_completion(job_id)

            # Download audio
            audio_data = await self._download_audio(job_id)

            # Create TTSAudio object
            audio = TTSAudio(
                audio_data=audio_data,
                content_type=f"audio/{kwargs.get('format', 'wav')}",
            )

            # Save to file if requested
            if output_path:
                audio.save(output_path)

            return audio

        except Exception as e:
            raise ProviderError(f"Failed to synthesize text: {e}") from e

    async def get_available_voices(self) -> List[TTSVoice]:
        """Get available voices.

        Returns:
            List of TTSVoice objects

        Raises:
            ProviderError: If voice list retrieval fails
        """
        try:
            # TODO: Implement voice list retrieval from Murf API
            # For now, return a basic list
            return [
                TTSVoice(
                    id="en-US-1",
                    name="English US Female 1",
                    gender="female",
                    language="en-US",
                    description="Professional female voice for US English",
                    tags=["professional", "female", "us-english"],
                ),
                TTSVoice(
                    id="en-US-2",
                    name="English US Male 1",
                    gender="male",
                    language="en-US",
                    description="Professional male voice for US English",
                    tags=["professional", "male", "us-english"],
                ),
            ]
        except Exception as e:
            raise ProviderError(f"Failed to get available voices: {e}") from e

    async def _create_tts_job(
        self,
        text: str,
        voice_id: str,
        rate: int,
        pitch: int,
        format: str,
    ) -> str:
        """Create TTS job.

        Args:
            text: Text to synthesize
            voice_id: Voice ID to use
            rate: Speech rate
            pitch: Voice pitch
            format: Output format

        Returns:
            Job ID

        Raises:
            ProviderError: If job creation fails
        """
        try:
            if not self._session:
                raise ProviderError("Provider not initialized")

            # Prepare request payload
            payload = {
                "text": text,
                "voice": voice_id,
                "rate": rate,
                "pitch": pitch,
                "format": format,
            }

            # Create job
            async with self._session.post("/tts/create", json=payload) as response:
                if response.status != 200:
                    error = await response.text()
                    raise ProviderError(f"Failed to create TTS job: {error}")

                data = await response.json()
                return data["job_id"]

        except Exception as e:
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(f"Failed to create TTS job: {e}") from e

    async def _get_job_status(self, job_id: str) -> str:
        """Get job status.

        Args:
            job_id: Job ID

        Returns:
            Job status

        Raises:
            ProviderError: If status check fails
        """
        try:
            if not self._session:
                raise ProviderError("Provider not initialized")

            async with self._session.get(f"/tts/status/{job_id}") as response:
                if response.status != 200:
                    error = await response.text()
                    raise ProviderError(f"Failed to get job status: {error}")

                data = await response.json()
                return data["status"]

        except Exception as e:
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(f"Failed to get job status: {e}") from e

    async def _wait_for_job_completion(self, job_id: str, timeout: int = 60) -> None:
        """Wait for job completion.

        Args:
            job_id: Job ID
            timeout: Timeout in seconds

        Raises:
            ProviderError: If job fails or times out
        """
        start_time = asyncio.get_event_loop().time()
        while True:
            status = await self._get_job_status(job_id)

            if status == "completed":
                return
            elif status == "failed":
                raise ProviderError(f"TTS job {job_id} failed")
            elif status == "error":
                raise ProviderError(f"TTS job {job_id} encountered an error")

            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise ProviderError(f"TTS job {job_id} timed out")

            # Wait before next check
            await asyncio.sleep(1)

    async def _download_audio(self, job_id: str) -> bytes:
        """Download audio data.

        Args:
            job_id: Job ID

        Returns:
            Audio data as bytes

        Raises:
            ProviderError: If download fails
        """
        try:
            if not self._session:
                raise ProviderError("Provider not initialized")

            async with self._session.get(f"/tts/download/{job_id}") as response:
                if response.status != 200:
                    error = await response.text()
                    raise ProviderError(f"Failed to download audio: {error}")

                return await response.read()

        except Exception as e:
            if isinstance(e, ProviderError):
                raise
            raise ProviderError(f"Failed to download audio: {e}") from e
