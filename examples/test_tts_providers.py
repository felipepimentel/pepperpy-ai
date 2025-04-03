#!/usr/bin/env python
"""
Test different TTS providers.

This example demonstrates the usage of different TTS providers
with a mock implementation.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional


class TTSVoice:
    """Voice for TTS providers."""

    def __init__(
        self,
        id: str,
        name: str,
        language: Optional[str] = None,
        gender: Optional[str] = None,
    ):
        self.id = id
        self.name = name
        self.language = language
        self.gender = gender


class MockTTSProvider:
    """Base mock TTS provider."""

    def __init__(self, **config):
        self.config = config
        self.initialized = False

        # Set provider name
        self.provider_name = self.__class__.__name__

        # Bind config to instance attributes
        for key, value in config.items():
            setattr(self, key, value)

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return

        print(f"Initializing {self.provider_name} with config: {self.config}")
        self.initialized = True

    async def get_available_voices(self) -> List[TTSVoice]:
        """Get available voices."""
        return []

    async def synthesize(
        self, text: str, voice_id: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Synthesize speech from text."""
        # This should be implemented by subclasses
        raise NotImplementedError("Subclasses must implement synthesize method")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        print(f"Cleaning up {self.provider_name}")
        self.initialized = False


class ElevenLabsProvider(MockTTSProvider):
    """ElevenLabs TTS provider."""

    async def get_available_voices(self) -> List[TTSVoice]:
        """Get available voices."""
        return [
            TTSVoice(id="Adam", name="Adam", gender="male", language="en-US"),
            TTSVoice(id="Rachel", name="Rachel", gender="female", language="en-US"),
            TTSVoice(id="Domi", name="Domi", gender="female", language="en-US"),
            TTSVoice(id="Antoni", name="Antoni", gender="male", language="en-US"),
        ]

    async def synthesize(
        self, text: str, voice_id: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Synthesize speech from text."""
        # Use voice_id from parameters or from config
        voice_id = voice_id or getattr(self, "voice", "Rachel")

        print(f"[ElevenLabs] Synthesizing: '{text}'")
        print(f"[ElevenLabs] Voice: {voice_id}")
        print(f"[ElevenLabs] Options: {options}")

        # Create mock output file path
        output_dir = Path("examples/output")
        output_dir.mkdir(exist_ok=True, parents=True)

        output_file = output_dir / f"elevenlabs_{hash(text) % 10000}.mp3"

        # Just create an empty file for demonstration
        with open(output_file, "wb") as f:
            f.write(b"")

        print(f"[ElevenLabs] Output saved to: {output_file}")

        return {
            "audio_file": str(output_file),
            "duration": len(text)
            / 15,  # Mock duration calculation (faster than others)
            "format": "mp3",
            "voice": voice_id,
            "text": text,
            "provider": "elevenlabs",
        }


class MurfProvider(MockTTSProvider):
    """Murf TTS provider."""

    async def get_available_voices(self) -> List[TTSVoice]:
        """Get available voices."""
        return [
            TTSVoice(id="en-US-male-1", name="Mike", gender="male", language="en-US"),
            TTSVoice(
                id="en-US-female-1", name="Sarah", gender="female", language="en-US"
            ),
            TTSVoice(id="en-GB-male-1", name="James", gender="male", language="en-GB"),
            TTSVoice(
                id="en-GB-female-1", name="Emma", gender="female", language="en-GB"
            ),
        ]

    async def synthesize(
        self, text: str, voice_id: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Synthesize speech from text."""
        # Use voice_id from parameters or from config
        voice_id = voice_id or getattr(self, "voice", "en-US-male-1")

        print(f"[Murf] Synthesizing: '{text}'")
        print(f"[Murf] Voice: {voice_id}")
        print(f"[Murf] Options: {options}")

        # Create mock output file path
        output_dir = Path("examples/output")
        output_dir.mkdir(exist_ok=True, parents=True)

        output_file = output_dir / f"murf_{hash(text) % 10000}.wav"

        # Just create an empty file for demonstration
        with open(output_file, "wb") as f:
            f.write(b"")

        print(f"[Murf] Output saved to: {output_file}")

        return {
            "audio_file": str(output_file),
            "duration": len(text) / 18,  # Mock duration calculation
            "format": "wav",
            "voice": voice_id,
            "text": text,
            "provider": "murf",
        }


class SystemProvider(MockTTSProvider):
    """System TTS provider."""

    async def get_available_voices(self) -> List[TTSVoice]:
        """Get available voices."""
        return [
            TTSVoice(
                id="system-male", name="System Male", gender="male", language="en"
            ),
            TTSVoice(
                id="system-female", name="System Female", gender="female", language="en"
            ),
        ]

    async def synthesize(
        self, text: str, voice_id: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Synthesize speech from text."""
        # Use voice_id from parameters or from config
        voice_id = voice_id or getattr(self, "voice", "system-male")

        print(f"[System] Synthesizing: '{text}'")
        print(f"[System] Voice: {voice_id}")
        print(f"[System] Options: {options}")

        # Create mock output file path
        output_dir = Path("examples/output")
        output_dir.mkdir(exist_ok=True, parents=True)

        output_file = output_dir / f"system_{hash(text) % 10000}.wav"

        # Just create an empty file for demonstration
        with open(output_file, "wb") as f:
            f.write(b"")

        print(f"[System] Output saved to: {output_file}")

        return {
            "audio_file": str(output_file),
            "duration": len(text)
            / 20,  # Mock duration calculation (slower than others)
            "format": "wav",
            "voice": voice_id,
            "text": text,
            "provider": "system",
        }


async def test_provider(
    provider_class, name: str, config: Dict[str, Any], test_text: str
):
    """Test a specific TTS provider."""
    print(f"\n=== Testing {name} Provider ===")

    # Create provider instance
    provider = provider_class(**config)

    # Initialize provider
    await provider.initialize()

    try:
        # Get available voices
        voices = await provider.get_available_voices()

        print(f"\n--- Available Voices ({len(voices)}) ---")
        for i, voice in enumerate(voices):
            print(f"{i+1}. {voice.name} (ID: {voice.id})")
            if voice.gender:
                print(f"   Gender: {voice.gender}")
            if voice.language:
                print(f"   Language: {voice.language}")

        if not voices:
            print("No voices available. Using default voice.")
            voice_id = None
        else:
            # Use the first voice
            voice_id = voices[0].id
            print(f"\nUsing voice: {voices[0].name}")

        # Synthesize speech
        print("\n--- Synthesizing Text ---")
        result = await provider.synthesize(
            text=test_text,
            voice_id=voice_id,
            speed=1.1,
            pitch=1.0,
            volume=1.0,
        )

        print("\n--- Result ---")
        print(f"Audio file: {result['audio_file']}")
        print(f"Duration: {result['duration']:.2f} seconds")
        print(f"Format: {result['format']}")
        print(f"Voice: {result['voice']}")
        print(f"Provider: {result.get('provider', name.lower())}")

    finally:
        # Clean up
        await provider.cleanup()


async def main():
    """Run the test for multiple TTS providers."""
    print("=== PepperPy TTS Providers Test ===")

    # Test text to synthesize
    test_text = "Hello! This is a test of the PepperPy text-to-speech system with different providers."

    # Test ElevenLabs provider
    await test_provider(
        ElevenLabsProvider,
        "ElevenLabs",
        {"api_key": "mock-key", "model": "eleven_monolingual_v1"},
        test_text,
    )

    # Test Murf provider
    await test_provider(
        MurfProvider,
        "Murf",
        {"api_key": "mock-key"},
        test_text,
    )

    # Test System provider (basic)
    await test_provider(
        SystemProvider,
        "System",
        {},
        test_text,
    )

    print("\nTTS providers test completed!")


if __name__ == "__main__":
    asyncio.run(main())
