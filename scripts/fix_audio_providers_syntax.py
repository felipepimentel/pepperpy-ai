#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe nos arquivos de provedores de áudio.
"""

import shutil
from datetime import datetime
from pathlib import Path

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = (
    BASE_DIR / "backups" / "audio_providers" / datetime.now().strftime("%Y%m%d_%H%M%S")
)


def create_backup(file_path):
    """Cria um backup do arquivo original."""
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir(parents=True)

    relative_path = file_path.relative_to(BASE_DIR)
    backup_path = BACKUP_DIR / relative_path

    # Criar diretórios necessários
    if not backup_path.parent.exists():
        backup_path.parent.mkdir(parents=True)

    # Copiar arquivo
    shutil.copy2(file_path, backup_path)
    print(f"Backup criado: {backup_path}")


def fix_google_tts_provider():
    """Corrige erros de sintaxe no arquivo google_tts.py."""
    file_path = (
        BASE_DIR
        / "pepperpy"
        / "multimodal"
        / "audio"
        / "providers"
        / "synthesis"
        / "google_tts.py"
    )

    if not file_path.exists():
        print(f"Arquivo não encontrado: {file_path}")
        return False

    create_backup(file_path)

    # Conteúdo corrigido
    corrected_content = """\"\"\"Google Text-to-Speech provider for synthesis capability.\"\"\"

import asyncio
import io
from pathlib import Path
from typing import Any, Optional, Union

from gtts import gTTS
from pydantic import BaseModel, Field

from pepperpy.multimodal.audio.base import (
    AudioConfig,
    AudioData,
    SynthesisError,
    SynthesisProvider,
)


class GTTSConfig(BaseModel):
    \"\"\"Configuration for gTTS provider.\"\"\"

    language: str = Field(default="en", description="Default language code")
    slow: bool = Field(default=False, description="Slow speech rate")
    format: str = Field(default="mp3", description="Output audio format")
    sample_rate: int = Field(default=24000, description="Sample rate in Hz")
    bit_depth: int = Field(default=16, description="Bit depth")
    channels: int = Field(default=1, description="Number of audio channels")


class GTTSProvider(SynthesisProvider):
    \"\"\"Google Text-to-Speech implementation.\"\"\"

    def __init__(self, **config: Any):
        \"\"\"Initialize provider with configuration.

        Args:
            **config: Configuration parameters

        Raises:
            SynthesisError: If configuration is invalid
        \"\"\"
        try:
            self.config = GTTSConfig(**config)
        except Exception as e:
            raise SynthesisError(
                "Failed to initialize gTTS provider",
                provider="gtts",
                details={"error": str(e)},
            ) from e

    async def synthesize(
        self,
        text: str,
        *,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        **kwargs: Any,
    ) -> AudioData:
        \"\"\"Synthesize text to speech using gTTS.

        Args:
            text: Text to synthesize
            language: Language code (overrides config)
            voice: Voice name (not used by gTTS)
            **kwargs: Additional parameters

        Returns:
            AudioData object with synthesized speech

        Raises:
            SynthesisError: If synthesis fails
        \"\"\"
        try:
            # Run gTTS in executor (blocking operation)
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_sync,
                text,
                language or self.config.language,
                kwargs.get("slow", self.config.slow),
            )

            # Create audio configuration
            config = AudioConfig(
                language=language or self.config.language,
                voice="default",  # gTTS doesn't support voice selection
                format=self.config.format,
                sample_rate=self.config.sample_rate,
                bit_depth=self.config.bit_depth,
                channels=self.config.channels,
            )

            # Return audio data
            return AudioData(
                content=audio_data,
                config=config,
                duration=0.0,  # gTTS doesn't provide duration info
                size=len(audio_data),
                metadata={
                    "provider": "gtts",
                    "slow": kwargs.get("slow", self.config.slow),
                },
            )

        except Exception as e:
            raise SynthesisError(
                "Failed to synthesize speech",
                provider="gtts",
                details={"error": str(e), "text": text},
            ) from e

    def _synthesize_sync(self, text: str, language: str, slow: bool) -> bytes:
        \"\"\"Synchronous gTTS synthesis.

        Args:
            text: Text to synthesize
            language: Language code
            slow: Whether to use slow speech rate

        Returns:
            Audio data as bytes
        \"\"\"
        # Create gTTS instance
        tts = gTTS(text=text, lang=language, slow=slow)
        
        # Save to buffer
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        
        return buffer.getvalue()

    async def save(
        self,
        audio: AudioData,
        path: Union[str, Path],
        **kwargs: Any,
    ) -> Path:
        \"\"\"Save audio data to file.

        Args:
            audio: Audio data to save
            path: Path to save to
            **kwargs: Additional parameters

        Returns:
            Path to saved file

        Raises:
            SynthesisError: If saving fails
        \"\"\"
        try:
            # Convert to Path
            path_obj = Path(path)
            
            # Create directory if it doesn't exist
            if not path_obj.parent.exists():
                path_obj.parent.mkdir(parents=True)
            
            # Write audio data to file
            with open(path_obj, "wb") as f:
                f.write(audio.content)
            
            return path_obj
            
        except Exception as e:
            raise SynthesisError(
                "Failed to save audio file",
                provider="gtts",
                details={"error": str(e), "path": str(path)},
            ) from e
"""

    # Escrever conteúdo corrigido
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(corrected_content)

    print(f"Arquivo corrigido: {file_path}")
    return True


def fix_google_transcription_provider():
    """Corrige erros de sintaxe no arquivo google_provider.py."""
    file_path = (
        BASE_DIR
        / "pepperpy"
        / "multimodal"
        / "audio"
        / "providers"
        / "transcription"
        / "google"
        / "google_provider.py"
    )

    if not file_path.exists():
        print(f"Arquivo não encontrado: {file_path}")
        return False

    create_backup(file_path)

    # Conteúdo corrigido
    corrected_content = """\"\"\"Google Cloud Speech-to-Text provider for transcription capability.\"\"\"

import os
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

from pepperpy.multimodal.audio.base import (
    TranscriptionError,
    TranscriptionProvider,
)


class GoogleTranscriptionProvider(TranscriptionProvider):
    \"\"\"Provider implementation for Google Cloud Speech-to-Text capabilities.\"\"\"

    def __init__(
        self,
        credentials: Optional[Dict[str, str]] = None,
        project_id: Optional[str] = None,
        **kwargs,
    ):
        \"\"\"Initialize Google Cloud Speech-to-Text provider.

        Args:
            credentials: Google Cloud credentials
            project_id: Google Cloud project ID
            **kwargs: Additional configuration parameters
        
        Raises:
            ImportError: If google-cloud-speech package is not installed
            TranscriptionError: If initialization fails
        \"\"\"
        try:
            # Import Google Cloud Speech
            from google.cloud import speech
        except ImportError:
            raise ImportError(
                "google-cloud-speech package is required for GoogleTranscriptionProvider. "
                "Install it with: pip install google-cloud-speech"
            ) from None

        self.kwargs = kwargs
        self.credentials = credentials
        self.project_id = project_id
        
        try:
            # Initialize client
            self.client = speech.SpeechClient()
        except Exception as e:
            raise TranscriptionError(f"Failed to initialize Google Cloud client: {e}") from e

    def transcribe(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> List[Dict]:
        \"\"\"Transcribe audio to text.

        Args:
            audio: Audio data as file path or bytes
            language: Language code (e.g., 'en-US')
            **kwargs: Additional parameters

        Returns:
            List of transcription segments

        Raises:
            TranscriptionError: If transcription fails
        \"\"\"
        try:
            from google.cloud import speech
            
            # Handle audio input
            audio_content = None
            if isinstance(audio, (str, Path)):
                with open(audio, "rb") as f:
                    audio_content = f.read()
            elif isinstance(audio, bytes):
                audio_content = audio
            else:
                raise ValueError(f"Unsupported audio type: {type(audio)}")
            
            # Create audio object
            audio_obj = speech.RecognitionAudio(content=audio_content)
            
            # Prepare config
            config = speech.RecognitionConfig(
                language_code=language or "en-US",
                **self.kwargs,
                **kwargs,
            )
            
            # Transcribe audio
            response = self.client.recognize(config=config, audio=audio_obj)
            
            # Process results
            segments = []
            for result in response.results:
                for alternative in result.alternatives:
                    segment = {
                        "text": alternative.transcript,
                        "confidence": alternative.confidence,
                        "start": 0.0,  # Basic recognize doesn't provide timestamps
                        "end": 0.0,
                    }
                    segments.append(segment)
            
            return segments
            
        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio: {e}") from e

    def transcribe_with_timestamps(
        self,
        audio: Union[str, Path, bytes],
        language: Optional[str] = None,
        **kwargs,
    ) -> List[Dict]:
        \"\"\"Transcribe audio with word-level timestamps.

        Args:
            audio: Audio data as file path or bytes
            language: Language code (e.g., 'en-US')
            **kwargs: Additional parameters

        Returns:
            List of transcription segments with timestamps

        Raises:
            TranscriptionError: If transcription fails
        \"\"\"
        try:
            from google.cloud import speech
            
            # Handle audio input
            audio_content = None
            if isinstance(audio, (str, Path)):
                with open(audio, "rb") as f:
                    audio_content = f.read()
            elif isinstance(audio, bytes):
                audio_content = audio
            else:
                raise ValueError(f"Unsupported audio type: {type(audio)}")
            
            # Create audio object
            audio_obj = speech.RecognitionAudio(content=audio_content)
            
            # Prepare config with word time offsets
            config = speech.RecognitionConfig(
                language_code=language or "en-US",
                enable_word_time_offsets=True,
                **self.kwargs,
                **kwargs,
            )
            
            # Transcribe audio
            response = self.client.recognize(config=config, audio=audio_obj)
            
            # Process results with timestamps
            segments = []
            for result in response.results:
                for alternative in result.alternatives:
                    words = []
                    for word_info in alternative.words:
                        word_data = {
                            "word": word_info.word,
                            "start": word_info.start_time.total_seconds(),
                            "end": word_info.end_time.total_seconds(),
                        }
                        words.append(word_data)
                    
                    # Create segment from words
                    if words:
                        segment = {
                            "text": alternative.transcript,
                            "confidence": alternative.confidence,
                            "start": words[0]["start"],
                            "end": words[-1]["end"],
                            "words": words,
                        }
                        segments.append(segment)
            
            return segments
            
        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio: {e}") from e

    def get_supported_languages(self) -> List[str]:
        \"\"\"Get list of supported language codes.

        Returns:
            List of supported language codes
        \"\"\"
        # Google Cloud Speech supports many languages
        # This is a subset of commonly used ones
        return [
            "en-US",  # English (United States)
            "en-GB",  # English (United Kingdom)
            "es-ES",  # Spanish (Spain)
            "es-US",  # Spanish (United States)
            "fr-FR",  # French
            "de-DE",  # German
            "it-IT",  # Italian
            "pt-BR",  # Portuguese (Brazil)
            "ru-RU",  # Russian
            "ja-JP",  # Japanese
            "ko-KR",  # Korean
            "zh-CN",  # Chinese (Simplified)
            "zh-TW",  # Chinese (Traditional)
            "ar-SA",  # Arabic
            "hi-IN",  # Hindi
        ]

    def get_supported_formats(self) -> List[str]:
        \"\"\"Get list of supported audio formats.

        Returns:
            List of supported audio format extensions
        \"\"\"
        return [
            "wav",
            "mp3",
            "flac",
            "ogg",
            "m4a",
            "aac",
            "amr",
            "amr-wb",
        ]
"""

    # Escrever conteúdo corrigido
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(corrected_content)

    print(f"Arquivo corrigido: {file_path}")
    return True


def main():
    """Função principal."""
    print("=== Corretor de Sintaxe de Provedores de Áudio ===")

    # Corrigir arquivos
    fixed_files = []

    if fix_google_tts_provider():
        fixed_files.append("google_tts.py")

    if fix_google_transcription_provider():
        fixed_files.append("google_provider.py")

    # Resumo
    print("\nProcesso concluído!")
    print(f"Arquivos corrigidos: {len(fixed_files)}")
    if fixed_files:
        print(f"Arquivos: {', '.join(fixed_files)}")
    print(f"Backups salvos em: {BACKUP_DIR}")


if __name__ == "__main__":
    main()
