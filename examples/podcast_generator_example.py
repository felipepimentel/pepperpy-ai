#!/usr/bin/env python
"""Example demonstrating podcast generation with PepperPy.

This example shows how to use PepperPy to create a podcast by:
1. Converting text to speech
2. Handling multiple speakers
3. Combining audio segments
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, List

from pepperpy import PepperPy

# Configurar diretórios
OUTPUT_DIR = Path("examples/output/tts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def create_podcast(title: str, segments: List[Dict[str, str]]) -> bytes:
    """Create a podcast from text segments.

    Args:
        title: Podcast title
        segments: List of segments with title, content, and speaker

    Returns:
        Combined audio bytes
    """
    # Development mode: No API keys needed if PEPPERPY_DEV__MODE=true
    # The TTS provider is controlled by PEPPERPY_TTS__PROVIDER
    test_mode = os.environ.get("PEPPERPY_DEV__MODE", "").lower() == "true"
    file_ext = "wav" if test_mode else "mp3"

    async with PepperPy().with_tts() as pepper:
        print(f"Gerando podcast: {title}")

        # Converter cada segmento em áudio
        audio_segments = []
        for i, segment in enumerate(segments):
            print(f"Processando segmento {i + 1}/{len(segments)}: {segment['title']}")

            # Ajustar voz com base no modo de teste
            voice_id = segment["speaker"]
            if test_mode:
                # Usar vozes do mock provider
                if "antonio" in voice_id.lower():
                    voice_id = "mock-male-en"
                else:
                    voice_id = "mock-female-en"

            # Gerar áudio usando a API fluente
            result = await (
                pepper.tts.with_text(segment["content"]).with_voice(voice_id).generate()
            )

            # Salvar segmento individual
            segment_file = OUTPUT_DIR / f"{title}_segment_{i + 1}.{file_ext}"
            segment_file.write_bytes(result.audio_data)
            print(f"  Segmento salvo em: {segment_file}")

            # Extrair os bytes de áudio do resultado
            audio_segments.append(result.audio_data)

        # Combinar segmentos (exemplo simplificado)
        # Em uma implementação real, você pode usar bibliotecas como pydub
        combined_audio = b"".join(audio_segments)

        # Salvar o arquivo combinado
        output_file = OUTPUT_DIR / f"{title}.{file_ext}"
        with open(output_file, "wb") as f:
            f.write(combined_audio)

        print(f"\nPodcast salvo em: {output_file}")
        return combined_audio


async def main() -> None:
    """Run the example."""
    print("Podcast Generator Example")
    print("=" * 50)

    # Verificar modo de teste
    test_mode = os.environ.get("PEPPERPY_DEV__MODE", "").lower() == "true"
    if test_mode:
        print("\nExecutando em MODO DE DESENVOLVIMENTO - usando provider mock")
        print("Nenhuma chamada de API real será feita")

    # Definir segmentos do podcast
    segments = [
        {
            "title": "Introdução",
            "content": "Bem-vindo ao nosso podcast sobre Python!",
            "speaker": "pt-BR-AntonioNeural",
        },
        {
            "title": "Conteúdo principal",
            "content": "Python é uma linguagem de programação versátil que pode ser usada para desenvolvimento web, análise de dados, inteligência artificial e muito mais.",
            "speaker": "pt-BR-FranciscaNeural",
        },
        {
            "title": "Conclusão",
            "content": "Obrigado por ouvir! Espero que tenha gostado do nosso podcast sobre Python.",
            "speaker": "pt-BR-AntonioNeural",
        },
    ]

    # Gerar podcast
    print("\nGerando podcast...")
    audio = await create_podcast("python_intro", segments)
    print(f"\nPodcast gerado: {len(audio)} bytes")


if __name__ == "__main__":
    # For automated testing, activate development mode:
    # export PEPPERPY_DEV__MODE=true
    # export PEPPERPY_TTS__PROVIDER=mock
    #
    # For production use, configure your TTS API keys in .env:
    # PEPPERPY_TTS__PROVIDER=azure (or elevenlabs, playht, murf)
    # PEPPERPY_TTS__AZURE__API_KEY=your_api_key
    # PEPPERPY_TTS__AZURE__REGION=your_region
    asyncio.run(main())
