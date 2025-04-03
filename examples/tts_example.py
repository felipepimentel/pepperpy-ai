#!/usr/bin/env python
"""
Text-to-Speech (TTS) Example.

This example demonstrates how to use the TTS subsystem 
with a mock implementation.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional


class MockTTSProvider:
    """Mock TTS provider."""

    def __init__(self, **config):
        self.config = config
        self.initialized = False

        # Bind config to instance attributes
        for key, value in config.items():
            setattr(self, key, value)

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return

        print(f"Initializing TTS provider with config: {self.config}")
        self.initialized = True

    async def synthesize(
        self, text: str, voice_id: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Synthesize speech from text."""
        # Use voice_id from parameters or from config
        voice_id = voice_id or getattr(self, "voice", "default")

        print(f"Synthesizing: '{text}'")
        print(f"Voice: {voice_id}")
        print(f"Options: {options}")

        # Create mock output file path
        output_dir = Path("examples/output")
        output_dir.mkdir(exist_ok=True, parents=True)

        output_file = output_dir / f"tts_output_{hash(text) % 10000}.mp3"

        # Just create an empty file for demonstration
        with open(output_file, "wb") as f:
            f.write(b"")

        print(f"Output saved to: {output_file}")

        return {
            "audio_file": str(output_file),
            "duration": len(text) / 20,  # Mock duration calculation
            "format": "mp3",
            "voice": voice_id,
            "text": text,
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        print("Cleaning up TTS provider")
        self.initialized = False


class TTSBuilder:
    """Fluent builder for TTS interactions."""

    def __init__(self, tts_provider: MockTTSProvider):
        self._tts = tts_provider
        self._text = None
        self._voice_id = None
        self._options = {
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0,
        }

    def with_text(self, text: str) -> "TTSBuilder":
        """Set text to synthesize."""
        self._text = text
        return self

    def with_voice(self, voice_id: str) -> "TTSBuilder":
        """Set voice to use."""
        self._voice_id = voice_id
        return self

    def with_speed(self, speed: float) -> "TTSBuilder":
        """Set speech speed."""
        self._options["speed"] = speed
        return self

    def with_pitch(self, pitch: float) -> "TTSBuilder":
        """Set voice pitch."""
        self._options["pitch"] = pitch
        return self

    def with_volume(self, volume: float) -> "TTSBuilder":
        """Set audio volume."""
        self._options["volume"] = volume
        return self

    async def generate(self) -> Dict[str, Any]:
        """Generate audio from text."""
        if not self._text:
            raise ValueError("Text must be set before generating audio")

        return await self._tts.synthesize(
            text=self._text, voice_id=self._voice_id, **self._options
        )


class PepperPy:
    """Mock PepperPy framework class."""

    def __init__(self):
        self._tts_provider = None
        self._providers = {}
        self._initialized = False

    def with_plugin(self, plugin_type: str, provider_type: str, **config) -> "PepperPy":
        """Configure a plugin."""
        if plugin_type == "tts":
            self._tts_provider = MockTTSProvider(**config)
            self._providers["tts"] = self._tts_provider
        return self

    @property
    def tts(self) -> TTSBuilder:
        """Get TTS builder."""
        if not self._tts_provider:
            raise ValueError("TTS provider not configured. Call with_plugin() first.")
        return TTSBuilder(self._tts_provider)

    async def initialize(self) -> None:
        """Initialize providers."""
        for provider in self._providers.values():
            await provider.initialize()

        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        for provider in self._providers.values():
            await provider.cleanup()

        self._initialized = False

    async def __aenter__(self) -> "PepperPy":
        """Enter async context."""
        await self.initialize()
        return self

    async def __aexit__(self, *args) -> None:
        """Exit async context."""
        await self.cleanup()


async def basic_tts_example():
    """Basic TTS example."""
    print("\n=== Basic TTS Example ===")

    # Create TTS provider directly
    tts_provider = MockTTSProvider(
        voice="en-US-Neural2-F",
        model="neural",
        quality="high",
    )

    # Initialize provider
    await tts_provider.initialize()

    try:
        # Generate speech
        print("\n--- Direct TTS Generation ---")
        result = await tts_provider.synthesize(
            text="Hello, world! This is a test of the text-to-speech system.",
            voice_id="en-US-Neural2-M",
            speed=1.2,
        )

        print(f"Result: {result}")

    finally:
        # Clean up
        await tts_provider.cleanup()


async def builder_pattern_example():
    """Example of using the builder pattern with TTS."""
    print("\n=== TTS Builder Pattern Example ===")

    # Create PepperPy instance
    pp = PepperPy()

    # Configure with TTS provider
    pp.with_plugin("tts", "elevenlabs", voice="Rachel")

    # Use context manager
    async with pp:
        # Using TTS builder
        print("\n--- TTS Builder ---")
        result = (
            await pp.tts.with_text(
                "Welcome to PepperPy! This is a demonstration of the text-to-speech functionality."
            )
            .with_voice("Josh")
            .with_speed(1.1)
            .with_pitch(0.9)
            .with_volume(1.5)
            .generate()
        )

        print(f"Result: {result}")


async def main():
    """Run the example."""
    print("=== PepperPy TTS Examples ===")

    await basic_tts_example()
    await builder_pattern_example()

    print("\nTTS examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
