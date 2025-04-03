#!/usr/bin/env python
"""Example demonstrating podcast generation with PepperPy.

This example shows how to use PepperPy to create a podcast
with multiple segments and speakers.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configure output directory
OUTPUT_DIR = Path("examples/output/tts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Podcast content segments
PODCAST_SEGMENTS = [
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


async def main():
    """Run the podcast generator example."""
    print("Podcast Generator Example")
    print("=" * 50)

    # Check for development mode
    test_mode = os.environ.get("PEPPERPY_DEV_MODE", "").lower() == "true"
    if test_mode:
        print("\nExecutando em MODO DE DESENVOLVIMENTO")
        print("Nenhuma chamada de API real será feita")

    # Initialize PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Generate podcast
        print("\nGerando podcast...")
        podcast_title = "python_intro"

        # Process each segment
        for i, segment in enumerate(PODCAST_SEGMENTS, 1):
            print(
                f"Processando segmento {i}/{len(PODCAST_SEGMENTS)}: {segment['title']}"
            )

            # Generate audio through PepperPy
            result = await app.execute(
                query="Generate speech from text",
                context={
                    "text": segment["content"],
                    "voice": segment["speaker"],
                    "output_format": "mp3",
                    "segment_id": i,
                    "podcast_title": podcast_title,
                },
            )

            print(f"  Segmento {i} processado: {result}")

        # Generate combined audio
        print("\nCombinando segmentos...")
        combined_result = await app.execute(
            query="Combine audio segments",
            context={
                "podcast_title": podcast_title,
                "num_segments": len(PODCAST_SEGMENTS),
            },
        )

        print(f"\nPodcast gerado: {combined_result}")

    finally:
        # Clean up resources
        await app.cleanup()


if __name__ == "__main__":
    # For automated testing, activate development mode:
    # export PEPPERPY_DEV_MODE=true
    #
    # For production use, configure your TTS API keys in .env:
    # PEPPERPY_TTS_PROVIDER=azure (or elevenlabs, playht, murf)
    asyncio.run(main())
