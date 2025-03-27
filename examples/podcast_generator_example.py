#!/usr/bin/env python
"""Example demonstrating podcast generation with PepperPy.

This example shows how to use PepperPy to create a podcast by:
1. Converting text to speech
2. Handling multiple speakers
3. Combining audio segments
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List

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
    # Configurar PepperPy para usar o provedor configurado no .env
    # A configuração vem de variáveis de ambiente no arquivo .env
    pepper = pepperpy.PepperPy().with_tts()

    async with pepper:
        print(f"Gerando podcast: {title}")

        # Converter cada segmento em áudio
        audio_segments = []
        for i, segment in enumerate(segments):
            print(f"Processando segmento {i + 1}/{len(segments)}: {segment['title']}")
            # A API retorna diferentes tipos dependendo do provedor
            result = await pepper.text_to_speech(
                text=segment["content"], voice_id=segment["speaker"]
            )

            # Extrair os bytes de áudio do resultado, independente do formato
            audio_bytes = extract_audio_bytes(result)
            audio_segments.append(audio_bytes)

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


def extract_audio_bytes(result: Any) -> bytes:
    """Extrai bytes de áudio do resultado, independente do formato.

    Args:
        result: Resultado da conversão texto para fala

    Returns:
        Bytes do áudio
    """
    # Caso 1: O resultado já é bytes
    if isinstance(result, bytes):
        return result

    # Caso 2: O resultado é um objeto TTSResult com atributo 'audio'
    if hasattr(result, "audio"):
        return result.audio

    # Caso 3: O resultado é um dicionário com chave 'audio'
    if isinstance(result, dict) and "audio" in result:
        return result["audio"]

    # Fallback: retornar bytes vazios se não for possível extrair
    print("AVISO: Não foi possível extrair áudio do resultado")
    return b""


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
