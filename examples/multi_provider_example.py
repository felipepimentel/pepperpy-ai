"""
PepperPy Multi-Provider Example.

Example of using multiple providers together with the PepperPy facade.
"""

import asyncio
import os

from pepperpy.facade import PepperPy
from pepperpy.tts.providers import AzureTTSProvider


class SimpleTTSExample:
    """Example class demonstrating TTS functionality."""

    def __init__(self, api_key: str, region: str = "eastus"):
        """Initialize the example.

        Args:
            api_key: Azure API key
            region: Azure region
        """
        self.api_key = api_key
        self.region = region
        self.pepperpy = PepperPy()

    async def run(self) -> None:
        """Run the example."""
        # Configure the framework with a TTS provider
        self.pepperpy.with_tts(
            AzureTTSProvider,
            api_key=self.api_key,
            region=self.region,
        )

        # Initialize all providers
        await self.pepperpy.initialize()

        # Use the TTS provider
        print("Getting available voices...")
        voices = await self.pepperpy.tts.get_voices()
        print(f"Found {len(voices)} voices")

        # Get the first English voice
        english_voices = [v for v in voices if v.get("locale", "").startswith("en-")]
        if not english_voices:
            print("No English voices found!")
            return

        voice = english_voices[0]
        print(f"Selected voice: {voice['id']} ({voice['name']})")

        # Convert text to speech
        text = "Hello, this is a test of the PepperPy framework's TTS functionality."
        print(f"Converting text to speech: '{text}'")

        audio_data = await self.pepperpy.tts.convert_text(
            text=text, voice_id=voice["id"]
        )

        print(f"Generated {len(audio_data)} bytes of audio data")

        # In a real application, you would save the audio data to a file
        # For demonstration purposes, we'll just print a message
        print("Audio conversion successful!")


class MultiProviderExample:
    """Example class demonstrating multiple providers."""

    def __init__(self, config_file: str | None = None):
        """Initialize the example.

        Args:
            config_file: Path to config file (optional)
        """
        # In a real application, you would load config from file
        # For now, we'll use a simple dictionary
        self.config = {
            "tts": {
                "api_key": os.environ.get("AZURE_API_KEY", "your-api-key"),
                "region": os.environ.get("AZURE_REGION", "eastus"),
            }
        }

        # Initialize the framework with our config
        self.pepperpy = PepperPy(config=self.config)

    async def run(self) -> None:
        """Run the example."""
        # Configure TTS by name (demonstrates provider name resolution)
        self.pepperpy.with_tts("azure")

        # Initialize everything
        await self.pepperpy.initialize()

        # Use the TTS provider
        voices = await self.pepperpy.tts.get_voices()
        print(f"Available voices: {len(voices)}")

        # For each module that has a provider configured,
        # you would access it through the corresponding property
        # For example:
        # - self.pepperpy.agent for agent functionality
        # - self.pepperpy.cache for caching functionality
        # - self.pepperpy.discovery for discovery functionality
        # - self.pepperpy.tool for tool functionality

        print("Example complete!")


async def main():
    """Run the multi-provider example."""
    # Check if we have a real Azure API key
    api_key = os.environ.get("AZURE_API_KEY")
    if api_key:
        # If we have a real API key, run the simple example
        example = SimpleTTSExample(api_key=api_key)
        await example.run()
    else:
        # Otherwise, run the multi-provider example
        # which uses mock functionality
        print("No Azure API key found. Running with mock functionality.")
        example = MultiProviderExample()
        await example.run()


if __name__ == "__main__":
    asyncio.run(main())
