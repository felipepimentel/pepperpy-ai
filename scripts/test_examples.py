#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para testar todos os exemplos do framework PepperPy.

Purpose:
    Verificar se todos os exemplos do framework estão funcionando corretamente.

Requirements:
    - Python 3.8+
    - PepperPy framework

Usage:
    python scripts/test_examples.py
"""

import os
import subprocess
import sys
from typing import List, Tuple


def find_examples(root_dir: str = "examples") -> List[str]:
    """Encontra todos os arquivos de exemplo Python.

    Args:
        root_dir: Diretório raiz para buscar exemplos

    Returns:
        Lista de caminhos para os arquivos de exemplo
    """
    examples = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                examples.append(os.path.join(root, file))

    return sorted(examples)


def run_example(example_path: str, timeout: int = 60) -> Tuple[bool, str]:
    """Executa um exemplo e retorna o resultado.

    Args:
        example_path: Caminho para o arquivo de exemplo
        timeout: Tempo máximo de execução em segundos

    Returns:
        Tupla com status de sucesso e saída do comando
    """
    print(f"\n{'=' * 80}")
    print(f"Executando: {example_path}")
    print(f"{'=' * 80}")

    try:
        result = subprocess.run(
            [sys.executable, example_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            print(f"✅ Sucesso: {example_path}")
            return True, result.stdout
        else:
            print(f"❌ Falha: {example_path}")
            print(f"Erro: {result.stderr}")
            return False, result.stderr

    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout: {example_path}")
        return False, "Timeout expired"
    except Exception as e:
        print(f"❌ Erro ao executar: {example_path}")
        print(f"Exceção: {str(e)}")
        return False, str(e)


def main() -> None:
    """Função principal."""
    # Encontrar todos os exemplos
    examples = find_examples()
    print(f"Encontrados {len(examples)} exemplos para testar.")

    # Resultados
    results = {"success": [], "failure": []}

    # Executar cada exemplo
    for example in examples:
        success, output = run_example(example)
        if success:
            results["success"].append(example)
        else:
            results["failure"].append((example, output))

    # Relatório final
    print("\n\n")
    print(f"{'=' * 80}")
    print("RELATÓRIO FINAL")
    print(f"{'=' * 80}")
    print(f"Total de exemplos: {len(examples)}")
    print(f"Sucessos: {len(results['success'])}")
    print(f"Falhas: {len(results['failure'])}")

    if results["failure"]:
        print("\nExemplos com falha:")
        for example, error in results["failure"]:
            print(f"- {example}")

    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
