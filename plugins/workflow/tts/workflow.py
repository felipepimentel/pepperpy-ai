"""
Text-to-Speech Workflow

This workflow provides a comprehensive interface for converting text to speech:
1. Converting text to audio
2. Streaming audio for real-time playback
3. Getting available voices
4. Customizing voice parameters
"""

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from pepperpy.utils.logging import get_logger
from pepperpy.workflow.provider import WorkflowProvider


class TTSWorkflow(WorkflowProvider):
    """Workflow for Text-to-Speech conversion using various providers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the TTS workflow.

        Args:
            config: Configuration parameters
        """
        self.config = config or {}

        # TTS configuration
        self.provider_name = self.config.get("provider", "azure")
        self.api_key = self.config.get(
            "api_key", os.environ.get(f"{self.provider_name.upper()}_API_KEY", "")
        )
        self.region = self.config.get("region", "eastus")
        self.voice_id = self.config.get("voice_id", "en-US-AriaNeural")
        self.voice_style = self.config.get("voice_style", "neutral")
        self.output_format = self.config.get("output_format", "mp3")

        # Output configuration
        self.save_files = self.config.get("save_files", True)
        self.output_dir = self.config.get("output_dir", "./output/tts")

        # Logging
        self.log_level = self.config.get("log_level", "INFO")
        self.log_to_console = self.config.get("log_to_console", True)
        self.logger = get_logger(
            __name__, level=self.log_level, console=self.log_to_console
        )

        # State
        self.tts_provider: Any = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize TTS provider and resources."""
        if self.initialized:
            return

        try:
            # Create output directory if needed and saving is enabled
            if self.save_files:
                os.makedirs(self.output_dir, exist_ok=True)

            # Import the appropriate provider based on configuration
            if self.provider_name == "azure":
                from pepperpy.tts import AzureTTSProvider

                # Initialize the Azure TTS provider
                self.tts_provider = AzureTTSProvider(
                    config={
                        "api_key": self.api_key,
                        "region": self.region,
                    }
                )
            elif self.provider_name == "elevenlabs":
                # Placeholder for ElevenLabs provider
                # from pepperpy.tts import ElevenLabsProvider
                # self.tts_provider = ElevenLabsProvider(
                #     config={
                #         "api_key": self.api_key,
                #     }
                # )
                raise ValueError("ElevenLabs provider not yet implemented")
            else:
                raise ValueError(f"Unsupported TTS provider: {self.provider_name}")

            # Initialize the provider
            await self.tts_provider.initialize()

            self.initialized = True
            self.logger.info(
                f"Initialized TTS workflow with {self.provider_name} provider"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS workflow: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized or self.tts_provider is None:
            return

        try:
            if hasattr(self.tts_provider, "cleanup"):
                await self.tts_provider.cleanup()
            self.tts_provider = None
            self.initialized = False
            self.logger.info("Cleaned up TTS workflow resources")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    async def _get_voices(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Get available voices from the TTS provider.

        Args:
            input_data: Input data with optional filters

        Returns:
            Dict containing available voices
        """
        if not self.initialized or self.tts_provider is None:
            await self.initialize()
            if not self.initialized:
                return {"error": "Failed to initialize TTS provider", "success": False}

        try:
            # Get voices with optional language filter
            language = input_data.get("language")

            # Call the provider's get_voices method
            voices = await self.tts_provider.get_voices()

            # Apply language filter if specified
            if language:
                voices = [
                    v for v in voices if language.lower() in v.get("id", "").lower()
                ]

            return {"voices": voices, "count": len(voices), "success": True}
        except Exception as e:
            self.logger.error(f"Error getting voices: {e}")
            return {"error": str(e), "success": False}

    async def _convert_text(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Convert text to speech.

        Args:
            input_data: Input data containing text and voice options

        Returns:
            Dict containing audio data or file path
        """
        if not self.initialized or self.tts_provider is None:
            await self.initialize()
            if not self.initialized:
                return {"error": "Failed to initialize TTS provider", "success": False}

        # Extract parameters from input
        text = input_data.get("text", "")
        if not text:
            return {"error": "No text provided", "success": False}

        voice_id = input_data.get("voice_id", self.voice_id)
        voice_style = input_data.get("voice_style", self.voice_style)
        output_file = input_data.get("output_file")

        # Get additional TTS parameters
        tts_params = input_data.get("parameters", {})

        try:
            # Convert text to speech
            audio_data = await self.tts_provider.convert_text(
                text=text, voice_id=voice_id, style=voice_style, **tts_params
            )

            result = {
                "audio_data": audio_data if not self.save_files else None,
                "audio_size": len(audio_data),
                "success": True,
                "voice_id": voice_id,
            }

            # Save to file if requested
            if self.save_files and output_file:
                file_path = Path(self.output_dir) / output_file
                with open(file_path, "wb") as f:
                    f.write(audio_data)
                result["file_path"] = str(file_path)
                self.logger.info(f"Saved audio to {file_path}")

            return result
        except Exception as e:
            self.logger.error(f"Error converting text to speech: {e}")
            return {"error": str(e), "success": False}

    async def _stream_text(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Stream text to speech in chunks.

        Args:
            input_data: Input data containing text and voice options

        Returns:
            Dict containing result summary
        """
        if not self.initialized or self.tts_provider is None:
            await self.initialize()
            if not self.initialized:
                return {"error": "Failed to initialize TTS provider", "success": False}

        # Extract parameters from input
        text = input_data.get("text", "")
        if not text:
            return {"error": "No text provided", "success": False}

        voice_id = input_data.get("voice_id", self.voice_id)
        voice_style = input_data.get("voice_style", self.voice_style)
        output_file = input_data.get("output_file")

        # Get additional TTS parameters
        tts_params = input_data.get("parameters", {})

        # Get the client output callback if available
        callback = input_data.get("callback")

        try:
            # Use the provider's streaming method
            chunks = []
            total_size = 0

            if hasattr(self.tts_provider, "convert_text_stream"):
                print("Streaming audio: ", end="", flush=True)

                async for chunk in self.tts_provider.convert_text_stream(
                    text=text, voice_id=voice_id, style=voice_style, **tts_params
                ):
                    # Call the callback if provided
                    if callback:
                        await callback(chunk)

                    chunks.append(chunk)
                    total_size += len(chunk)

                    # Print progress indicator
                    if not callback:
                        print(".", end="", flush=True)

                if not callback:
                    print(" Done!")
            else:
                # Fall back to non-streaming for providers that don't support it
                self.logger.warning(
                    "Streaming not supported, falling back to standard conversion"
                )
                audio_data = await self.tts_provider.convert_text(
                    text=text, voice_id=voice_id, style=voice_style, **tts_params
                )
                chunks = [audio_data]
                total_size = len(audio_data)

            # Save to file if requested
            file_path = None
            if self.save_files and output_file:
                file_path = Path(self.output_dir) / output_file
                with open(file_path, "wb") as f:
                    for chunk in chunks:
                        f.write(chunk)
                self.logger.info(f"Saved audio to {file_path}")

            return {
                "success": True,
                "chunks": len(chunks),
                "total_size": total_size,
                "voice_id": voice_id,
                "file_path": str(file_path) if file_path else None,
            }
        except Exception as e:
            self.logger.error(f"Error streaming text to speech: {e}")
            return {"error": str(e), "success": False}

    async def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Execute the TTS workflow.

        Args:
            data: Input data with task and parameters

        Returns:
            Results of the workflow execution
        """
        try:
            # Initialize if not already initialized
            if not self.initialized:
                await self.initialize()

            # Get task and input
            task = data.get("task", "")
            input_data = data.get("input", {})

            # Handle different tasks
            if task == "get_voices":
                return await self._get_voices(input_data)
            elif task == "convert_text":
                return await self._convert_text(input_data)
            elif task == "stream_text":
                return await self._stream_text(input_data)
            else:
                return {"error": f"Unsupported task: {task}", "success": False}
        except Exception as e:
            self.logger.error(f"Workflow execution error: {e}")
            return {"error": str(e), "success": False}
        finally:
            # We don't cleanup after each execution to allow for
            # reuse of the provider for multiple conversions
            pass

    async def stream(self, data: dict[str, Any]) -> AsyncGenerator[bytes, None]:
        """Stream audio data from the TTS workflow.

        Args:
            data: Input data with task and parameters

        Yields:
            Chunks of audio data
        """
        # Initialize if not already initialized
        if not self.initialized or self.tts_provider is None:
            await self.initialize()
            if not self.initialized:
                yield b""
                return

        # Make sure the task is for streaming
        task = data.get("task", "")
        if task != "stream_text":
            yield f"Streaming only supported for 'stream_text' task, not '{task}'".encode()
            return

        # Extract input data
        input_data = data.get("input", {})
        text = input_data.get("text", "")
        if not text:
            yield b"No text provided for streaming"
            return

        voice_id = input_data.get("voice_id", self.voice_id)
        voice_style = input_data.get("voice_style", self.voice_style)

        # Get additional TTS parameters
        tts_params = input_data.get("parameters", {})

        try:
            # Use the provider's streaming method if available
            if hasattr(self.tts_provider, "convert_text_stream"):
                async for chunk in self.tts_provider.convert_text_stream(
                    text=text, voice_id=voice_id, style=voice_style, **tts_params
                ):
                    yield chunk
            else:
                # Fall back to non-streaming for providers that don't support it
                audio_data = await self.tts_provider.convert_text(
                    text=text, voice_id=voice_id, style=voice_style, **tts_params
                )
                yield audio_data
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
            yield f"Error: {e!s}".encode()
