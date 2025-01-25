"""Tool for text-to-speech using ElevenLabs API."""

import os
from typing import Any, Literal

import aiohttp
from pydantic import BaseModel

from pepperpy.tools.tool import Tool, ToolResult


OutputFormat = Literal[
    "mp3_22050_32",
    "mp3_44100_32",
    "mp3_44100_64",
    "mp3_44100_96",
    "mp3_44100_128",
    "mp3_44100_192",
    "pcm_16000",
    "pcm_22050",
    "pcm_24000",
    "pcm_44100",
    "ulaw_8000",
]


class ElevenLabsConfig(BaseModel):
    """Configuration for ElevenLabs."""

    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default voice - Rachel
    model_id: str = "eleven_monolingual_v1"
    optimize_streaming_latency: int = 0
    output_format: OutputFormat = "mp3_44100_128"  # High quality MP3


class ElevenLabsTool(Tool):
    """Tool for text-to-speech using ElevenLabs API."""

    def __init__(self, config: ElevenLabsConfig | None = None) -> None:
        """Initialize ElevenLabs tool.
        
        Args:
            config: Optional tool configuration
        """
        self.config = config or ElevenLabsConfig()
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is not set")
        
        self.session: aiohttp.ClientSession | None = None

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession(
            base_url="https://api.elevenlabs.io/",
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            },
        )

    async def text_to_speech(self, text: str, output_path: str) -> None:
        """Convert text to speech.
        
        Args:
            text: Text to convert
            output_path: Path to save audio file
            
        Raises:
            Exception: If conversion fails
        """
        if not self.session:
            raise RuntimeError("Tool not initialized")

        data = {
            "text": text,
            "model_id": self.config.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        print(f"\nSending request to ElevenLabs API...")
        print(f"Text length: {len(text)} characters")

        async with self.session.post(
            f"v1/text-to-speech/{self.config.voice_id}",
            json=data,
            params={
                "optimize_streaming_latency": self.config.optimize_streaming_latency,
                "output_format": self.config.output_format,
            },
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"API request failed ({response.status}): {text}")

            # Save audio file
            with open(output_path, "wb") as f:
                f.write(await response.read())

            print(f"Audio saved to: {output_path}")

    async def execute(self, **kwargs: Any) -> ToolResult[str]:
        """Execute text-to-speech conversion.
        
        Args:
            text: Text to convert
            output_path: Path to save audio file
            
        Returns:
            Tool execution result with output file path
        """
        text = kwargs.get("text", "")
        output_path = kwargs.get("output_path", "output.mp3")
        
        try:
            await self.text_to_speech(text, output_path)
            return ToolResult(success=True, data=output_path, error=None)
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None 