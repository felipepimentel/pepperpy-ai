#!/usr/bin/env python3
"""Exemplo de agentes inteligentes utilizando PepperPy.

Este exemplo demonstra como criar agentes inteligentes que podem interagir
com o ambiente, tomar decisões e executar tarefas utilizando a framework PepperPy.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretório de saída
OUTPUT_DIR = Path(__file__).parent / "output" / "agents"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main():
    """Executar o exemplo de agentes inteligentes."""
    print("Exemplo de Agentes Inteligentes")
    print("=" * 50)

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Definir tarefas para os agentes executarem
        tasks = [
            "Encontrar e resumir as últimas notícias sobre inteligência artificial",
            "Analisar os prós e contras de diferentes frameworks de machine learning",
            "Criar uma lista de verificação para implementar um sistema de IA ética",
        ]

        # Executar tarefas com agentes
        for i, task in enumerate(tasks, 1):
            print(f"\nTarefa {i}: {task}")
            print("-" * 50)

            # Executar tarefa através do agente PepperPy
            result = await app.execute(
                query="Executar esta tarefa utilizando agentes inteligentes",
                context={"task": task, "agent_type": "research"},
            )

            # Exibir resultado resumido
            print("\nResultado (resumo):")
            preview = (
                " ".join(result.split()[:30]) if result else "Nenhum resultado gerado"
            )
            print(f"{preview}...")

            # Salvar resultado em arquivo
            output_file = OUTPUT_DIR / f"tarefa_{i}_resultado.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"Tarefa: {task}\n\n")
                f.write(f"Resultado:\n{result}")

            print(f"\nResultado completo salvo em: {output_file}")

        # Demonstração de agente interativo
        print("\nDemonstrando agente interativo...")

        messages = [
            "Quero criar um aplicativo de IA para ajudar pessoas a aprenderem idiomas",
            "Que tecnologias devo considerar?",
            "Como posso implementar um sistema de recomendação personalizada?",
        ]

        conversation_history = []

        for i, message in enumerate(messages, 1):
            print(f"\nMensagem {i}: {message}")

            # Adicionar mensagem ao histórico
            conversation_history.append({"role": "user", "content": message})

            # Obter resposta do agente
            response = await app.execute(
                query="Responder ao usuário como um assistente de desenvolvimento",
                context={
                    "conversation": conversation_history,
                    "agent_type": "assistant",
                },
            )

            # Exibir resposta
            print(f"\nResposta do Agente: {response}")

            # Adicionar resposta ao histórico
            conversation_history.append({"role": "assistant", "content": response})

        # Salvar conversa completa
        output_file = OUTPUT_DIR / "conversa_agente.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Conversa com Agente Inteligente\n\n")

            for entry in conversation_history:
                role = "Usuário" if entry["role"] == "user" else "Agente"
                f.write(f"{role}: {entry['content']}\n\n")

        print(f"\nConversa completa salva em: {output_file}")

        print("\nExemplo de agentes inteligentes concluído!")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
