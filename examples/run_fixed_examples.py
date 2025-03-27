#!/usr/bin/env python
"""Script para executar os exemplos corrigidos do PepperPy.

Este script executa os exemplos principais do PepperPy
que devem funcionar com as configurações fornecidas.
"""

import asyncio
import os
import subprocess
import sys

from dotenv import load_dotenv

# Garantir que estamos no diretório correto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Carregar variáveis de ambiente
load_dotenv()


# Criar diretórios necessários
def create_directories():
    """Criar diretórios necessários para os exemplos."""
    dirs = [
        "data/chroma",
        "data/storage",
        "output/tts",
        "output/bi_assistant",
        "output/repos",
        "output/workflow",
    ]

    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Diretório criado: {directory}")


# Exemplos que devem funcionar com as configurações atuais
WORKING_EXAMPLES = [
    "minimal_example.py",
    "document_processing_example.py",
    "repo_analysis_assistant_example.py",
    "ai_learning_assistant_example.py",
]


async def run_example(filename):
    """Executar um exemplo específico do PepperPy."""
    print("\n" + "=" * 70)
    print(f"Executando: {filename}")
    print("=" * 70)

    try:
        # Executar como um módulo Python
        result = subprocess.run(
            [sys.executable, filename],
            capture_output=True,
            text=True,
            timeout=180,  # Timeout de 3 minutos
        )

        # Imprimir saída
        if result.stdout:
            print("\nSaída:")
            print(result.stdout)

        if result.stderr:
            print("\nErros:")
            print(result.stderr)

        if result.returncode == 0:
            print(f"\n✅ Exemplo {filename} executado com sucesso!")
        else:
            print(f"\n❌ Exemplo {filename} falhou com código {result.returncode}")

    except subprocess.TimeoutExpired:
        print(f"\n⚠️ Exemplo {filename} excedeu o tempo limite de execução (3 minutos)")
    except Exception as e:
        print(f"\n❌ Erro ao executar {filename}: {e}")

    # Aguardar um momento entre os exemplos para garantir limpeza de recursos
    await asyncio.sleep(1)


async def main():
    """Executar os exemplos funcionais."""
    print("PepperPy - Executor de Exemplos Funcionais")
    print("=" * 50)

    # Criar diretórios necessários
    create_directories()

    # Executar cada exemplo da lista de exemplos funcionais
    for example in WORKING_EXAMPLES:
        await run_example(example)

    print("\n" + "=" * 70)
    print("Execução dos exemplos concluída!")
    print("=" * 70)


if __name__ == "__main__":
    # Executar a função principal
    asyncio.run(main())
