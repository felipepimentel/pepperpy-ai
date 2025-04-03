#!/usr/bin/env python
"""Exemplo de assistente de pesquisa em tempo real.

Este exemplo demonstra como usar PepperPy para:
1. Realizar consultas na web em tempo real
2. Extrair informações relevantes
3. Gerar resumos e respostas baseadas nas informações coletadas
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretórios para saída
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output" / "research"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main():
    """Executar exemplo de pesquisa em tempo real."""
    print("Assistente de Pesquisa em Tempo Real")
    print("=" * 50)

    # Perguntas de pesquisa para demonstração
    research_queries = [
        "Quais são as últimas tecnologias em inteligência artificial?",
        "Como a mudança climática está afetando a agricultura?",
    ]

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Processar cada consulta
        for i, query in enumerate(research_queries, 1):
            print(f"\nConsulta {i}: {query}")
            print("-" * 50)

            # Etapa 1: Buscar informações na web
            print("\nBuscando informações na web...")
            search_result = await app.execute(
                query="Buscar informações recentes sobre este tópico",
                context={"topic": query},
            )

            print(f"Informações encontradas: {search_result}")

            # Etapa 2: Analisar informações e extrair dados relevantes
            print("\nAnalisando e extraindo dados relevantes...")
            analysis = await app.execute(
                query="Analisar estas informações e extrair dados relevantes",
                context={"information": search_result, "topic": query},
            )

            print(f"Análise: {analysis}")

            # Etapa 3: Gerar resposta completa
            print("\nGerando resposta completa...")
            response = await app.execute(
                query="Gerar resposta detalhada com base na análise",
                context={"analysis": analysis, "topic": query},
            )

            print(f"\nResposta: {response}")

            # Salvar resultado em arquivo
            output_file = OUTPUT_DIR / f"pesquisa_{i}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"Consulta: {query}\n\n")
                f.write(f"Informações coletadas:\n{search_result}\n\n")
                f.write(f"Análise:\n{analysis}\n\n")
                f.write(f"Resposta:\n{response}")

            print(f"\nResultado salvo em: {output_file}")

            # Breve pausa entre consultas
            if i < len(research_queries):
                print("\nPreparando próxima consulta...")
                await asyncio.sleep(1)

        print("\nExemplo de pesquisa concluído!")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
