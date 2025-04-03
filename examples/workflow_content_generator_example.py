#!/usr/bin/env python3
"""Exemplo de geração de conteúdo com PepperPy.

Este exemplo demonstra como usar PepperPy para gerar conteúdo sobre tópicos específicos
em diferentes estilos e formatos.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretório de saída
OUTPUT_DIR = Path(__file__).parent / "output" / "content"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main():
    """Executar o exemplo de geração de conteúdo."""
    print("Exemplo de Gerador de Conteúdo")
    print("=" * 50)

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Gerar conteúdo sobre IA
        print("\nGerando conteúdo sobre 'Inteligência Artificial'...")

        # Executar consulta através do PepperPy
        result = await app.execute(
            query="Gerar conteúdo sobre Inteligência Artificial",
            context={
                "topic": "Inteligência Artificial",
                "style": "conversacional",
                "format": "artigo",
            },
        )

        # Exibir prévia do resultado
        print("\nConteúdo gerado (prévia):")
        print("-" * 50)
        preview = result.split("\n\n")[0] if result else "Nenhum conteúdo gerado"
        print(f"{preview}...")
        print("-" * 50)

        # Salvar resultado
        output_file = OUTPUT_DIR / "conteudo_ia.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\nConteúdo salvo em: {output_file}")

        # Experimentar com opções diferentes
        print("\nGerando conteúdo com opções diferentes...")
        advanced_result = await app.execute(
            query="Gerar conteúdo sobre Ética em Machine Learning",
            context={
                "topic": "Ética em Machine Learning",
                "style": "informativo",
                "format": "post_blog",
            },
        )

        # Salvar resultado com opções avançadas
        output_file = OUTPUT_DIR / "etica_ml_conteudo.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(advanced_result)
        print(f"\nConteúdo avançado salvo em: {output_file}")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
