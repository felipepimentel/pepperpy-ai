#!/usr/bin/env python3
"""Exemplo de Assistente de Aprendizado com IA.

Um exemplo minimalista mostrando como usar PepperPy.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretório de saída
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output" / "learning_assistant"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main():
    """Executar o exemplo de assistente de aprendizado com IA."""
    print("Exemplo Minimalista PepperPy")
    print("=" * 50)

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Consultas de aprendizado
        perguntas = [
            "Qual é a função de decoradores em Python?",
            "Explique o conceito de compreensão de lista em Python",
            "Como funcionam os geradores em Python?",
        ]

        # Processar cada pergunta
        for i, pergunta in enumerate(perguntas, 1):
            print(f"\nPergunta {i}: {pergunta}")
            print("-" * 50)

            # Executar consulta simples
            resultado = await app.execute(query=pergunta)
            print(f"\nResposta: {resultado}")

            # Salvar resultado
            arquivo_saida = OUTPUT_DIR / f"pergunta_{i}_resposta.txt"
            with open(arquivo_saida, "w", encoding="utf-8") as f:
                f.write(f"Pergunta: {pergunta}\n\n")
                f.write(f"Resposta:\n{resultado}")

            print(f"Resposta salva em: {arquivo_saida}")

        # Executar consulta com feedback
        print("\nExecutando consulta com contexto de aprendizado...")
        feedback = await app.execute(
            query="Resumir os conceitos de Python aprendidos até agora",
            context={"perguntas_anteriores": perguntas},
        )

        print(f"\nResumo de aprendizado: {feedback}")

        # Salvar resumo
        arquivo_resumo = OUTPUT_DIR / "resumo_aprendizado.txt"
        with open(arquivo_resumo, "w", encoding="utf-8") as f:
            f.write("RESUMO DE CONCEITOS APRENDIDOS\n")
            f.write("=" * 30 + "\n\n")
            f.write(feedback)

        print(f"Resumo salvo em: {arquivo_resumo}")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
