#!/usr/bin/env python
"""Script para executar todos os exemplos do PepperPy.

Este script configura o ambiente e executa todos os exemplos disponíveis
no diretório examples, mostrando o resultado de cada um.
"""

import asyncio
import os
import subprocess
import sys

from dotenv import load_dotenv

# Garantir que estamos no diretório correto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Carregar variáveis de ambiente
load_dotenv(".env")


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


def get_example_files():
    """Obter a lista de arquivos de exemplos Python."""
    example_files = []

    for file in os.listdir("."):
        if (
            file.endswith("_example.py")
            and os.path.isfile(file)
            and not file.startswith("__")
        ):
            example_files.append(file)

    # Adicionar o exemplo minimal primeiro (mais simples)
    if "minimal_example.py" in example_files:
        example_files.remove("minimal_example.py")
        example_files.insert(0, "minimal_example.py")

    return example_files


async def run_example(filename):
    """Executar um exemplo específico do PepperPy."""
    print("\n" + "=" * 70)
    print(f"Executando: {filename}")
    print("=" * 70)

    try:
        # Tentativa 1: Executar como um módulo Python
        result = subprocess.run(
            [sys.executable, filename],
            capture_output=True,
            text=True,
            timeout=120,  # Timeout de 2 minutos
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
        print(f"\n⚠️ Exemplo {filename} excedeu o tempo limite de execução (2 minutos)")
    except Exception as e:
        print(f"\n❌ Erro ao executar {filename}: {e}")

    # Aguardar um momento entre os exemplos para garantir limpeza de recursos
    await asyncio.sleep(1)


async def main():
    """Executar todos os exemplos disponíveis."""
    print("PepperPy - Executor de Exemplos")
    print("=" * 50)

    # Criar diretórios necessários
    create_directories()

    # Obter lista de exemplos
    examples = get_example_files()
    print(f"Encontrados {len(examples)} exemplos para executar:\n")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")

    # Executar cada exemplo
    for example in examples:
        await run_example(example)

    print("\n" + "=" * 70)
    print("Execução de todos os exemplos concluída!")
    print("=" * 70)


if __name__ == "__main__":
    # Executar a função principal
    asyncio.run(main())
