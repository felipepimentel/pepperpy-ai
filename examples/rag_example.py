#!/usr/bin/env python3
"""Exemplo de RAG (Recuperação Aumentada por Geração) com PepperPy.

Este exemplo demonstra como utilizar o sistema RAG do PepperPy para
melhorar as respostas do modelo de linguagem com informações recuperadas.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretório de saída
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output" / "rag"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Documentos de exemplo
DOCUMENTOS = [
    "Python é uma linguagem de programação de alto nível conhecida por sua legibilidade e versatilidade.",
    "PepperPy é um framework Python para construir aplicações de IA com uma interface unificada.",
    "Recuperação Aumentada por Geração (RAG) combina recuperação e geração para resultados mais precisos.",
    "Modelos de linguagem grandes (LLMs) são redes neurais treinadas em conjuntos massivos de dados de texto.",
    "O sistema RAG do PepperPy permite melhorar as respostas com conhecimento específico de domínio.",
    "Os plugins do PepperPy seguem um padrão de provedor com métodos de ciclo de vida comuns.",
]

# Consultas de exemplo
CONSULTAS = [
    "O que é PepperPy?",
    "Como funciona o sistema RAG?",
    "Quais são as características do Python?",
]


async def main():
    """Executar o exemplo de RAG."""
    print("Exemplo de Recuperação Aumentada por Geração (RAG)")
    print("=" * 50)

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    # Preparar arquivo de resultados
    arquivo_resultados = OUTPUT_DIR / "resultados_rag.txt"
    with open(arquivo_resultados, "w", encoding="utf-8") as f:
        f.write("RESULTADOS DE RAG COM PEPPERPY\n")
        f.write("=" * 30 + "\n\n")

    try:
        # 1. Configurar base de conhecimento
        print("\nConfigurando base de conhecimento...")

        for i, documento in enumerate(DOCUMENTOS, 1):
            print(f"Adicionando documento {i}/{len(DOCUMENTOS)}")
            await app.execute(
                query="Adicionar documento à base de conhecimento",
                context={
                    "texto": documento,
                    "metadata": {"id": f"doc_{i}", "fonte": "exemplo"},
                },
            )

        # 2. Exemplo básico de RAG
        print("\n=== Exemplo Básico de RAG ===")

        # Processar cada consulta
        for i, consulta in enumerate(CONSULTAS, 1):
            print(f"\nConsulta {i}: {consulta}")
            print("-" * 50)

            # Executar RAG para a consulta
            resultado = await app.execute(
                query=consulta, context={"usar_rag": True, "limite": 2}
            )

            print(f"Resposta: {resultado}")

            # Salvar no arquivo de resultados
            with open(arquivo_resultados, "a", encoding="utf-8") as f:
                f.write(f"Consulta {i}: {consulta}\n")
                f.write("-" * 30 + "\n")
                f.write(f"Resposta:\n{resultado}\n\n")

        # 3. RAG com parâmetros avançados
        print("\n=== RAG com Parâmetros Avançados ===")

        consulta_avancada = "Explique como o PepperPy implementa RAG e como isso se compara a outros frameworks"

        print(f"Consulta avançada: {consulta_avancada}")
        print("-" * 50)

        resultado_avancado = await app.execute(
            query=consulta_avancada,
            context={
                "usar_rag": True,
                "limite": 3,
                "limiar_similaridade": 0.7,
                "incluir_metadata": True,
                "formato": "markdown",
            },
        )

        print(f"Resposta: {resultado_avancado}")

        # Salvar no arquivo de resultados
        with open(arquivo_resultados, "a", encoding="utf-8") as f:
            f.write("RAG COM PARÂMETROS AVANÇADOS\n")
            f.write("-" * 30 + "\n")
            f.write(f"Consulta: {consulta_avancada}\n\n")
            f.write(f"Resposta:\n{resultado_avancado}\n\n")

        # 4. Comparação com e sem RAG
        print("\n=== Comparação Com e Sem RAG ===")

        consulta_comparacao = "O que são LLMs e como eles funcionam?"

        print(f"Consulta para comparação: {consulta_comparacao}")
        print("-" * 50)

        # Sem RAG
        resultado_sem_rag = await app.execute(
            query=consulta_comparacao, context={"usar_rag": False}
        )

        print(f"Resposta SEM RAG: {resultado_sem_rag}")

        # Com RAG
        resultado_com_rag = await app.execute(
            query=consulta_comparacao, context={"usar_rag": True, "limite": 3}
        )

        print(f"Resposta COM RAG: {resultado_com_rag}")

        # Salvar no arquivo de resultados
        with open(arquivo_resultados, "a", encoding="utf-8") as f:
            f.write("COMPARAÇÃO COM E SEM RAG\n")
            f.write("-" * 30 + "\n")
            f.write(f"Consulta: {consulta_comparacao}\n\n")
            f.write(f"Resposta SEM RAG:\n{resultado_sem_rag}\n\n")
            f.write(f"Resposta COM RAG:\n{resultado_com_rag}\n\n")

        print(f"\nTodos os resultados foram salvos em: {arquivo_resultados}")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
