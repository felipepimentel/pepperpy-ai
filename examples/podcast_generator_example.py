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

from pepperpy import PepperPy

# Configurar diretórios
OUTPUT_DIR = Path("output/tts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def create_podcast(title: str, segments: List[Dict[str, str]]) -> bytes:
    """Create a podcast from text segments.

    Args:
        title: Podcast title
        segments: List of segments with title, content, and speaker

    Returns:
        Combined audio bytes
    """
    # Configuração do provedor vem das variáveis de ambiente
    async with PepperPy().with_tts() as pepper:
        print(f"Gerando podcast: {title}")

        # Converter cada segmento em áudio
        audio_segments = []
        for i, segment in enumerate(segments):
            print(f"Processando segmento {i + 1}/{len(segments)}: {segment['title']}")

            # Gerar áudio usando a API fluente
            result = await (
                pepper.tts.with_text(segment["content"])
                .with_voice(segment["speaker"])
                .generate()
            )

            # Extrair os bytes de áudio do resultado
            audio_segments.append(result.audio)

        # Combinar segmentos (exemplo simplificado)
        # Em uma implementação real, você pode usar bibliotecas como pydub
        combined_audio = b"".join(audio_segments)

        # Salvar o arquivo combinado
        output_file = OUTPUT_DIR / f"{title}.mp3"
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
    # Required environment variables in .env file:
    # PEPPERPY_TTS__PROVIDER=azure
    # PEPPERPY_TTS__API_KEY=your_api_key
    # PEPPERPY_TTS__REGION=your_region
    asyncio.run(main())
