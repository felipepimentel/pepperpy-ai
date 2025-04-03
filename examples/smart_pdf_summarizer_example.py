#!/usr/bin/env python3
"""Exemplo de sumarização inteligente de PDFs.

Este exemplo demonstra como usar PepperPy para:
1. Carregar um documento PDF
2. Extrair seu conteúdo
3. Gerar um resumo inteligente
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretórios
EXAMPLES_DIR = Path(__file__).parent
INPUT_DIR = EXAMPLES_DIR / "input" / "docs"
OUTPUT_DIR = EXAMPLES_DIR / "output" / "pdf_summaries"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Definir PDF de exemplo
EXAMPLE_PDF = "exemplo.pdf"  # Substitua pelo nome de um arquivo PDF real


async def main():
    """Executar exemplo de sumarização de PDF."""
    print("Sumarizador Inteligente de PDFs")
    print("=" * 50)

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        pdf_path = INPUT_DIR / EXAMPLE_PDF
        print(f"\nProcessando PDF: {pdf_path}")

        # Verificar se o arquivo existe
        if not pdf_path.exists():
            print(
                "Arquivo não encontrado. Criando um PDF de exemplo para demonstração."
            )
            # Em um caso real, você carregaria um PDF existente
            content = (
                "Este é um conteúdo de exemplo que simula o texto extraído de um PDF."
            )
        else:
            # Extrair conteúdo do PDF
            print("Extraindo conteúdo do PDF...")
            content = await app.execute(
                query="Extrair conteúdo de um documento PDF",
                context={"pdf_path": str(pdf_path)},
            )

        print(f"\nConteúdo extraído ({len(content)} caracteres)")

        # Gerar resumo
        print("\nGerando resumo inteligente...")
        summary = await app.execute(
            query="Gerar um resumo conciso e informativo deste conteúdo",
            context={"content": content},
        )

        # Exibir resumo
        print("\nResumo gerado:")
        print("-" * 50)
        print(summary)
        print("-" * 50)

        # Salvar resumo
        output_file = OUTPUT_DIR / f"{Path(EXAMPLE_PDF).stem}_resumo.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Resumo de: {EXAMPLE_PDF}\n\n")
            f.write(summary)

        print(f"\nResumo salvo em: {output_file}")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
