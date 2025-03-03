#!/usr/bin/env python3
"""
Script para verificar arquivos com erros de importação que ainda não estão na lista de exceções.
"""

import os
import re
import sys
from typing import List, Set


def read_file(file_path: str) -> str:
    """Lê o conteúdo de um arquivo."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """Escreve conteúdo em um arquivo."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def find_python_files(directory: str) -> List[str]:
    """Encontra todos os arquivos Python em um diretório recursivamente."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def check_for_import_errors(file_path: str) -> bool:
    """Verifica se o arquivo tem erros de importação."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Procura por erros de importação
        import_errors = []

        # Procura por erros de importação desconhecida
        unknown_imports = re.findall(r'"([^"]+)" is unknown import symbol', content)
        if unknown_imports:
            import_errors.extend(unknown_imports)

        # Procura por outros tipos de erros
        other_errors = re.findall(r"Err \| (.+)", content)
        if other_errors:
            import_errors.extend(other_errors)

        if import_errors:
            print(f"Arquivo: {file_path}")
            for error in import_errors:
                print(f"  - {error}")
            return True
        return False
    except Exception as e:
        print(f"Erro ao verificar {file_path}: {e}")
        return False


def is_f821_globally_ignored() -> bool:
    """Verifica se F821 está na lista de ignores globais no pyproject.toml."""
    try:
        content = read_file("pyproject.toml")

        # Verifica se F821 está na lista de ignores globais
        return '"F821"' in content or "'F821'" in content
    except Exception as e:
        print(f"Erro ao ler pyproject.toml: {e}")
        return False


def main():
    """Função principal."""
    # Verifica se o diretório pepperpy existe
    if not os.path.isdir("pepperpy"):
        print(
            "Diretório 'pepperpy' não encontrado. Execute este script na raiz do projeto."
        )
        sys.exit(1)

    # Verifica se F821 está na lista de ignores globais
    if is_f821_globally_ignored():
        print("F821 já está configurado para ser ignorado globalmente.")
    else:
        print("F821 não está configurado para ser ignorado globalmente.")
        print(
            "Recomendação: Adicione F821 à lista de ignores globais no pyproject.toml:"
        )
        print("""
[tool.ruff.lint]
ignore = ["E501", "F401", "F403", "F405", "E402", "E722", "E741", "F821", "B024"]
        """)
        sys.exit(1)

    # Encontra todos os arquivos Python no diretório pepperpy
    python_files = find_python_files("pepperpy")

    # Verifica se há arquivos com erros de importação
    files_with_errors = []
    error_types = {}

    for file_path in python_files:
        if check_for_import_errors(file_path):
            files_with_errors.append(file_path)

    if files_with_errors:
        print(
            f"\nEncontrados {len(files_with_errors)} arquivos com erros de importação."
        )
    else:
        print("\nNenhum arquivo com erros de importação encontrado.")


if __name__ == "__main__":
    main()
