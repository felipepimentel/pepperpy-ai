#!/usr/bin/env python3
"""Exemplo de processamento de conteúdo com PepperPy.

Este exemplo demonstra como utilizar PepperPy para processar diferentes
tipos de conteúdo, incluindo texto, áudio e imagens.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretórios
EXAMPLES_DIR = Path(__file__).parent
INPUT_DIR = EXAMPLES_DIR / "input" / "content"
OUTPUT_DIR = EXAMPLES_DIR / "output" / "processed_content"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Exemplo de conteúdos
SAMPLE_TEXT = """
A inteligência artificial (IA) está revolucionando diversas indústrias.
Machine learning, processamento de linguagem natural e visão computacional
são algumas das tecnologias que estão transformando a maneira como interagimos
com computadores e automatizamos tarefas.
"""

SAMPLE_IMAGE_DESCRIPTION = "Uma imagem mostrando um gráfico de crescimento de tecnologias de IA ao longo do tempo."
SAMPLE_AUDIO_DESCRIPTION = (
    "Um áudio contendo uma entrevista sobre o futuro da inteligência artificial."
)


async def main():
    """Executar o exemplo de processamento de conteúdo."""
    print("Exemplo de Processamento de Conteúdo")
    print("=" * 50)

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # 1. Processamento de texto
        print("\nProcessando conteúdo de texto...")
        text_result = await app.execute(
            query="Analisar e melhorar este texto sobre IA",
            context={"content": SAMPLE_TEXT, "content_type": "text"},
        )

        print("\nResultado do processamento de texto:")
        print("-" * 50)
        print(text_result)

        # Salvar resultado
        text_output_file = OUTPUT_DIR / "texto_processado.txt"
        with open(text_output_file, "w", encoding="utf-8") as f:
            f.write(text_result)
        print(f"\nTexto processado salvo em: {text_output_file}")

        # 2. Processamento de imagem (simulado)
        print("\nProcessando descrição de imagem...")
        image_result = await app.execute(
            query="Extrair insights desta descrição de imagem",
            context={
                "content": SAMPLE_IMAGE_DESCRIPTION,
                "content_type": "image_description",
            },
        )

        print("\nResultado do processamento da imagem:")
        print("-" * 50)
        print(image_result)

        # Salvar resultado
        image_output_file = OUTPUT_DIR / "imagem_processada.txt"
        with open(image_output_file, "w", encoding="utf-8") as f:
            f.write(image_result)
        print(f"\nResultado do processamento de imagem salvo em: {image_output_file}")

        # 3. Processamento de áudio (simulado)
        print("\nProcessando descrição de áudio...")
        audio_result = await app.execute(
            query="Gerar resumo deste conteúdo de áudio",
            context={
                "content": SAMPLE_AUDIO_DESCRIPTION,
                "content_type": "audio_description",
            },
        )

        print("\nResultado do processamento de áudio:")
        print("-" * 50)
        print(audio_result)

        # Salvar resultado
        audio_output_file = OUTPUT_DIR / "audio_processado.txt"
        with open(audio_output_file, "w", encoding="utf-8") as f:
            f.write(audio_result)
        print(f"\nResultado do processamento de áudio salvo em: {audio_output_file}")

        # 4. Processamento multimodal (combinando os resultados)
        print("\nRealizando processamento multimodal...")
        multimodal_result = await app.execute(
            query="Integrar os resultados dos diferentes tipos de conteúdo",
            context={
                "text_result": text_result,
                "image_result": image_result,
                "audio_result": audio_result,
            },
        )

        print("\nResultado do processamento multimodal:")
        print("-" * 50)
        print(multimodal_result)

        # Salvar resultado final
        final_output_file = OUTPUT_DIR / "resultado_multimodal.txt"
        with open(final_output_file, "w", encoding="utf-8") as f:
            f.write("# Resultado da Análise Multimodal\n\n")
            f.write(multimodal_result)
        print(f"\nResultado multimodal salvo em: {final_output_file}")

        print("\nExemplo de processamento de conteúdo concluído!")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
