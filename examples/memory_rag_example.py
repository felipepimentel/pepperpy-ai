#!/usr/bin/env python3
"""Exemplo de RAG em memória com PepperPy.

Este exemplo demonstra como usar PepperPy para implementar funcionalidades de
Recuperação Aumentada por Geração (RAG) em memória, sem necessidade de
dependências externas ou bancos de dados.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretório de saída
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output" / "memory_rag"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Documentos de exemplo para o índice RAG
DOCUMENTOS_EXEMPLO = [
    "Python é uma linguagem de programação de alto nível, interpretada e de propósito geral.",
    "A linguagem Python foi criada por Guido van Rossum e lançada em 1991.",
    "Python enfatiza a legibilidade do código com sua sintaxe clara e expressiva.",
    "Django é um framework web de alto nível escrito em Python que incentiva o desenvolvimento rápido.",
    "Flask é um microframework Python para desenvolvimento web, simples e leve.",
    "Pandas é uma biblioteca Python usada para manipulação e análise de dados.",
    "NumPy é uma biblioteca Python que suporta arrays multidimensionais e funções matemáticas.",
    "A filosofia de design do Python está resumida no 'The Zen of Python'.",
    "PepperPy é um framework para simplificar o desenvolvimento de aplicações baseadas em IA.",
]

# Consultas de exemplo para o sistema RAG
CONSULTAS_EXEMPLO = [
    "O que é Python?",
    "Quem criou a linguagem Python?",
    "Quais são os principais frameworks web em Python?",
    "Como o Python lida com análise de dados?",
    "O que é PepperPy?",
]


async def main():
    """Executar o exemplo de RAG em memória."""
    print("Exemplo de Recuperação Aumentada por Geração (RAG) em Memória")
    print("=" * 70)

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    # Arquivo para salvar resultados
    arquivo_resultados = OUTPUT_DIR / "resultados_rag.txt"
    with open(arquivo_resultados, "w", encoding="utf-8") as f:
        f.write("RESULTADOS DE RECUPERAÇÃO AUMENTADA POR GERAÇÃO\n")
        f.write("=" * 50 + "\n\n")

    try:
        # 1. Adicionar documentos à base de conhecimento
        print(
            f"\nAdicionando {len(DOCUMENTOS_EXEMPLO)} documentos à base de conhecimento..."
        )

        for i, documento in enumerate(DOCUMENTOS_EXEMPLO):
            await app.execute(
                query="Adicionar documento à base de conhecimento",
                context={
                    "documento": documento,
                    "metadata": {"id": i, "fonte": "exemplo"},
                },
            )

        print("Documentos adicionados com sucesso!")

        # 2. Processar cada consulta usando RAG
        print("\nExecutando consultas com sistema RAG...")

        for i, consulta in enumerate(CONSULTAS_EXEMPLO, 1):
            print(f"\nConsulta {i}: {consulta}")
            print("-" * 50)

            # Executar consulta RAG
            resposta = await app.execute(
                query=consulta, context={"usar_rag": True, "top_k": 3}
            )

            print(f"Resposta: {resposta}")

            # Salvar no arquivo de resultados
            with open(arquivo_resultados, "a", encoding="utf-8") as f:
                f.write(f"Consulta {i}: {consulta}\n")
                f.write("-" * 40 + "\n")
                f.write(f"Resposta:\n{resposta}\n\n")

        # 3. Executar consulta com controle avançado
        print("\nExecutando consulta RAG com parâmetros avançados...")

        consulta_avancada = "Compare Python com outras linguagens de programação"

        resposta_avancada = await app.execute(
            query=consulta_avancada,
            context={
                "usar_rag": True,
                "top_k": 5,
                "limiar_similaridade": 0.6,
                "modo": "semantic",
            },
        )

        print(f"\nConsulta avançada: {consulta_avancada}")
        print(f"Resposta: {resposta_avancada}")

        # Salvar no arquivo de resultados
        with open(arquivo_resultados, "a", encoding="utf-8") as f:
            f.write("CONSULTA AVANÇADA\n")
            f.write("-" * 40 + "\n")
            f.write(f"Consulta: {consulta_avancada}\n")
            f.write(f"Resposta:\n{resposta_avancada}\n\n")

        print(f"\nTodos os resultados foram salvos em: {arquivo_resultados}")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
