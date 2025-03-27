#!/usr/bin/env python
"""Example demonstrating podcast generation with PepperPy.

This example shows how to use PepperPy to create a podcast by:
1. Converting text to speech
2. Handling multiple speakers
3. Combining audio segments
"""

import asyncio
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

import pepperpy

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()


async def create_podcast(title: str, segments: List[Dict[str, str]]) -> bytes:
    """Create a podcast from text segments.

    Args:
        title: Podcast title
        segments: List of segments with title, content, and speaker

    Returns:
        Combined audio bytes
    """
    # Configurar PepperPy para usar o provedor mockado
    # A configuração vem de variáveis de ambiente no arquivo .env
    pepper = pepperpy.PepperPy().with_tts()

    async with pepper:
        print(f"Gerando podcast: {title}")

        # Converter cada segmento em áudio
        audio_segments = []
        for i, segment in enumerate(segments):
            print(f"Processando segmento {i + 1}/{len(segments)}: {segment['title']}")
            audio_result = await pepper.text_to_speech(
                text=segment["content"], voice_id=segment["speaker"]
            )
            # O objeto audio_result pode ser um TTSResult ou bytes, dependendo da implementação
            if hasattr(audio_result, "audio"):
                audio_segments.append(audio_result.audio)
            else:
                # Se for bytes diretamente
                audio_segments.append(audio_result)

        # Combinar segmentos (exemplo simplificado)
        # Em uma implementação real, você pode usar bibliotecas como pydub
        combined_audio = b"".join(audio_segments)

        # Salvar o arquivo combinado
        output_dir = Path("output/tts")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{title}.mp3"

        with open(output_file, "wb") as f:
            f.write(combined_audio)

        print(f"\nPodcast salvo em: {output_file}")

        return combined_audio


async def main() -> None:
    """Run the example."""
    print("Podcast Generator Example")
    print("=" * 50)

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
    # Variáveis de ambiente necessárias (definidas no arquivo .env):
    # PEPPERPY_TTS__PROVIDER=mock ou PEPPERPY_TTS__PROVIDER=murf
    asyncio.run(main())
