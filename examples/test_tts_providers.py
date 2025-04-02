"""Test script for TTS providers."""

import asyncio
import os

from pepperpy.plugins import discover_plugins, ensure_discovery_initialized
from pepperpy.plugins import create_provider_instance
from pepperpy.tts.base import TTSProvider


async def test_mock_provider():
    """Test the mock TTS provider."""
    print("\nTesting Mock TTS Provider...")

    # Set environment variables for mock provider
    os.environ["PEPPERPY_DEV__MODE"] = "true"
    os.environ["PEPPERPY_TTS__PROVIDER"] = "mock"

    provider = create_provider_instance("tts", "mock")
    if not isinstance(provider, TTSProvider):
        print("Error: Provider is not a TTSProvider")
        return

    await provider.initialize()

    try:
        audio_data = await provider.synthesize(
            "This is a test of the mock TTS provider"
        )
        output_path = "output/mock_speech.wav"
        os.makedirs("output", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_data.audio_data)
        print(f"Mock TTS audio saved to: {output_path}")
    finally:
        await provider.cleanup()


async def test_elevenlabs_provider():
    """Test the ElevenLabs TTS provider."""
    print("\nTesting ElevenLabs TTS Provider...")

    api_key = os.environ.get("PEPPERPY_TTS__ELEVENLABS_API_KEY")
    if not api_key:
        print("Skipping ElevenLabs test - API key not found")
        return

    provider = create_provider_instance(
        "tts", "elevenlabs", api_key=api_key
    )
    await provider.initialize()

    try:
        audio_data = await provider.synthesize("Hello from ElevenLabs!")
        output_path = "output/elevenlabs_speech.mp3"
        os.makedirs("output", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_data)
        print(f"ElevenLabs audio saved to: {output_path}")
    finally:
        await provider.cleanup()


async def test_azure_provider():
    """Test the Azure TTS provider."""
    print("\nTesting Azure TTS Provider...")

    api_key = os.environ.get("PEPPERPY_TTS__AZURE_API_KEY")
    region = os.environ.get("PEPPERPY_TTS__AZURE_REGION")

    if not (api_key and region):
        print("Skipping Azure test - API key or region not found")
        return

    provider = create_provider_instance(
        "tts", "azure", api_key=api_key, region=region
    )
    await provider.initialize()

    try:
        audio_data = await provider.synthesize("Hello from Azure!")
        output_path = "output/azure_speech.mp3"
        os.makedirs("output", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_data)
        print(f"Azure audio saved to: {output_path}")
    finally:
        await provider.cleanup()


async def test_murf_provider():
    """Test the Murf TTS provider."""
    print("\nTesting Murf TTS Provider...")

    provider = create_provider_instance("tts", "murf")
    await provider.initialize()

    try:
        audio_data = await provider.synthesize("Hello from Murf!")
        output_path = "output/murf_speech.mp3"
        os.makedirs("output", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_data)
        print(f"Murf audio saved to: {output_path}")
    except Exception as e:
        print(f"Murf test failed: {e}")
    finally:
        await provider.cleanup()


async def test_playht_provider():
    """Test the PlayHT TTS provider."""
    print("\nTesting PlayHT TTS Provider...")

    provider = create_provider_instance("tts", "playht")
    await provider.initialize()

    try:
        audio_data = await provider.synthesize("Hello from PlayHT!")
        output_path = "output/playht_speech.mp3"
        os.makedirs("output", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_data)
        print(f"PlayHT audio saved to: {output_path}")
    except Exception as e:
        print(f"PlayHT test failed: {e}")
    finally:
        await provider.cleanup()


async def main():
    """Run all TTS provider tests."""
    print("Starting TTS provider tests...")

    # Discover plugins
    from pepperpy.plugins.registry import register_plugin_path
    register_plugin_path("plugins")
    await ensure_discovery_initialized()

    await test_mock_provider()
    await test_elevenlabs_provider()
    await test_azure_provider()
    await test_murf_provider()
    await test_playht_provider()

    print("\nAll tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
