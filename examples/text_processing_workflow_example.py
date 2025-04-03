#!/usr/bin/env python3
"""Exemplo de fluxo de processamento de texto com PepperPy.

Este exemplo demonstra como utilizar PepperPy para fluxos de processamento de texto.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretório de saída
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output" / "text_workflow"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Corpus de exemplo com textos
CORPUS_EXEMPLO = [
    "Python é uma linguagem de programação versátil criada por Guido van Rossum em 1991.",
    "O framework Django é escrito em Python e permite o desenvolvimento rápido de aplicações web seguras e escaláveis.",
    "NumPy é essencial para computação científica em Python, fornecendo suporte para arrays multidimensionais e operações matemáticas.",
    "Machine Learning é um subcampo da Inteligência Artificial focado no desenvolvimento de algoritmos que podem aprender a partir de dados.",
    "PepperPy é um framework de IA para simplificar o desenvolvimento de aplicações baseadas em LLMs.",
]


async def main():
    """Executar os exemplos de processamento de texto com PepperPy."""
    print("Exemplo de Processamento de Texto com PepperPy")
    print("=" * 50)

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    # Preparar arquivo de resultados
    arquivo_resultados = OUTPUT_DIR / "resultados_processamento.txt"
    with open(arquivo_resultados, "w", encoding="utf-8") as f:
        f.write("Resultados do Processamento de Texto\n")
        f.write("=" * 50 + "\n\n")

    try:
        # Processar texto com funcionalidade semelhante a RAG
        print("\n=== Processamento de Texto com Base de Conhecimento ===")

        # Adicionar ao arquivo de resultados
        with open(arquivo_resultados, "a", encoding="utf-8") as f:
            f.write("PROCESSAMENTO COM BASE DE CONHECIMENTO\n")
            f.write("-" * 40 + "\n\n")

        # Adicionar documentos à base de conhecimento
        print(f"Adicionando {len(CORPUS_EXEMPLO)} documentos ao contexto...")

        # Executar consulta para adicionar documentos
        for i, texto in enumerate(CORPUS_EXEMPLO):
            await app.execute(
                query="Adicionar documento à base de conhecimento",
                context={
                    "texto": texto,
                    "metadata": {"fonte": "exemplo", "id": str(i)},
                },
            )

        # Consulta sobre Python
        print("\nConsultando sobre Python...")
        resposta_python = await app.execute(
            query="O que é Python e quem o criou?",
            context={"usar_base_conhecimento": True},
        )
        print(f"Resposta: {resposta_python}")

        # Salvar no arquivo de resultados
        with open(arquivo_resultados, "a", encoding="utf-8") as f:
            f.write("Consulta: O que é Python e quem o criou?\n")
            f.write(f"Resposta: {resposta_python}\n\n")

        # Consulta sobre Machine Learning
        print("\nConsultando sobre Machine Learning...")
        resposta_ml = await app.execute(
            query="Explique o que é Machine Learning em poucas palavras.",
            context={"usar_base_conhecimento": True},
        )
        print(f"Resposta: {resposta_ml}")

        # Salvar no arquivo de resultados
        with open(arquivo_resultados, "a", encoding="utf-8") as f:
            f.write("Consulta: Explique o que é Machine Learning em poucas palavras.\n")
            f.write(f"Resposta: {resposta_ml}\n\n")

        # Processar texto com pipeline personalizado
        print("\n=== Processamento de Texto com Pipeline Personalizado ===")

        # Adicionar ao arquivo de resultados
        with open(arquivo_resultados, "a", encoding="utf-8") as f:
            f.write("PROCESSAMENTO COM PIPELINE PERSONALIZADO\n")
            f.write("-" * 40 + "\n\n")

        # Textos de exemplo para processar
        textos_exemplo = [
            "Python é uma linguagem de programação versátil com sintaxe clara e legível.",
            "Processamento de Linguagem Natural (PLN) permite aos computadores entenderem a linguagem humana.",
        ]

        print("Processando textos com pipeline personalizado...")
        for i, texto in enumerate(textos_exemplo, 1):
            # Transformar e resumir texto
            resultado = await app.execute(
                query="Resumir este texto em uma frase", context={"texto": texto}
            )
            print(f"Resumo {i}: {resultado}")

            # Salvar no arquivo de resultados
            with open(arquivo_resultados, "a", encoding="utf-8") as f:
                f.write(f"Texto {i}: {texto}\n")
                f.write(f"Resumo: {resultado}\n\n")

        print(f"\nTodos os resultados foram salvos em: {arquivo_resultados}")

    finally:
        # Limpar recursos
        await app.cleanup()

    print("\nExemplos de processamento de texto concluídos.")


if __name__ == "__main__":
    asyncio.run(main())
