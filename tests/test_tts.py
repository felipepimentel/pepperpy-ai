"""Tests for the TTS module."""

import os
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from pepperpy.tts import AzureTTSProvider, TTSComponent, TTSVoiceError


@pytest.fixture
def mock_speech_config():
    """Create a mock Azure speech config."""
    return MagicMock()


@pytest.fixture
def mock_speech_synthesizer():
    """Create a mock Azure speech synthesizer."""
    return MagicMock()


@pytest.fixture
def mock_synthesis_result():
    """Create a mock Azure synthesis result."""
    result = MagicMock()
    result.audio_data = b"test_audio_data"
    return result


@pytest.fixture
def mock_voices_result():
    """Create a mock Azure voices result."""
    voice = MagicMock()
    voice.short_name = "en-US-JennyNeural"
    voice.local_name = "Jenny"
    voice.locale = "en-US"
    voice.gender = "Female"
    voice.style_list = ["chat", "cheerful"]
    voice.voice_path = "16000"

    result = MagicMock()
    result.voices = [voice]
    return result


@pytest.fixture
def provider(mock_speech_config):
    """Create a TTS provider instance."""
    provider = AzureTTSProvider()
    provider._client = mock_speech_config
    return provider


@pytest.fixture
def component(provider):
    """Create a TTS component instance."""
    return TTSComponent(
        id="test-tts",
        name="Test TTS",
        provider=provider,
        config={
            "voice": "en-US-JennyNeural",
            "output_format": "audio-16khz-128kbitrate-mono-mp3",
        },
    )


@pytest.mark.asyncio
async def test_provider_initialization():
    """Test provider initialization."""
    with (
        patch.dict(
            os.environ,
            {
                "AZURE_SPEECH_KEY": "test_key",
                "AZURE_SPEECH_REGION": "test_region",
            },
        ),
        patch("azure.cognitiveservices.speech.SpeechConfig") as mock_config,
    ):
        provider = AzureTTSProvider()
        await provider.initialize()

        mock_config.assert_called_once_with(
            subscription="test_key",
            region="test_region",
        )
        assert provider._client is not None


@pytest.mark.asyncio
async def test_provider_cleanup(provider):
    """Test provider cleanup."""
    await provider.cleanup()
    assert provider._client is None


@pytest.mark.asyncio
async def test_synthesize(provider, mock_speech_synthesizer, mock_synthesis_result):
    """Test text synthesis."""
    with patch(
        "azure.cognitiveservices.speech.SpeechSynthesizer",
        return_value=mock_speech_synthesizer,
    ):
        mock_speech_synthesizer.speak_text_async.return_value.get.return_value = (
            mock_synthesis_result
        )

        audio_data = await provider.synthesize(
            text="Hello, world!",
            voice="en-US-JennyNeural",
            output_format="audio-16khz-128kbitrate-mono-mp3",
        )

        assert audio_data == b"test_audio_data"
        mock_speech_synthesizer.speak_text_async.assert_called_once_with(
            "Hello, world!"
        )


@pytest.mark.asyncio
async def test_convert_text(provider, mock_speech_synthesizer, mock_synthesis_result):
    """Test text conversion."""
    with patch(
        "azure.cognitiveservices.speech.SpeechSynthesizer",
        return_value=mock_speech_synthesizer,
    ):
        mock_speech_synthesizer.speak_text_async.return_value.get.return_value = (
            mock_synthesis_result
        )

        audio_data = await provider.convert_text(
            text="Hello, world!",
            voice_id="en-US-JennyNeural",
        )

        assert audio_data == b"test_audio_data"
        mock_speech_synthesizer.speak_text_async.assert_called_once_with(
            "Hello, world!"
        )


@pytest.mark.asyncio
async def test_convert_text_stream(
    provider, mock_speech_synthesizer, mock_synthesis_result
):
    """Test text streaming."""
    with patch(
        "azure.cognitiveservices.speech.SpeechSynthesizer",
        return_value=mock_speech_synthesizer,
    ):
        mock_speech_synthesizer.speak_text_async.return_value.get.return_value = (
            mock_synthesis_result
        )

        chunks: List[bytes] = []
        async for chunk in provider.convert_text_stream(
            text="Hello, world!",
            voice_id="en-US-JennyNeural",
            chunk_size=4,
        ):
            chunks.append(chunk)

        assert b"".join(chunks) == b"test_audio_data"
        mock_speech_synthesizer.speak_text_async.assert_called_once_with(
            "Hello, world!"
        )


@pytest.mark.asyncio
async def test_get_voices(provider, mock_speech_synthesizer, mock_voices_result):
    """Test getting available voices."""
    with patch(
        "azure.cognitiveservices.speech.SpeechSynthesizer",
        return_value=mock_speech_synthesizer,
    ):
        mock_speech_synthesizer.get_voices_async.return_value.get.return_value = (
            mock_voices_result
        )

        voices = await provider.get_voices()

        assert len(voices) == 1
        voice = voices[0]
        assert voice["id"] == "en-US-JennyNeural"
        assert voice["name"] == "Jenny"
        assert voice["locale"] == "en-US"
        assert voice["gender"] == "Female"
        assert voice["style_list"] == ["chat", "cheerful"]
        assert voice["sample_rate"] == "16000"


@pytest.mark.asyncio
async def test_clone_voice(provider):
    """Test voice cloning (not supported)."""
    with pytest.raises(TTSVoiceError) as exc_info:
        await provider.clone_voice(
            name="test_voice",
            samples=[b"test_audio"],
        )

    assert "not supported" in str(exc_info.value)


@pytest.mark.asyncio
async def test_component_process(
    component, mock_speech_synthesizer, mock_synthesis_result
):
    """Test component processing."""
    with patch(
        "azure.cognitiveservices.speech.SpeechSynthesizer",
        return_value=mock_speech_synthesizer,
    ):
        mock_speech_synthesizer.speak_text_async.return_value.get.return_value = (
            mock_synthesis_result
        )

        audio_data = await component.process("Hello, world!")

        assert audio_data == b"test_audio_data"
        mock_speech_synthesizer.speak_text_async.assert_called_once_with(
            "Hello, world!"
        )
