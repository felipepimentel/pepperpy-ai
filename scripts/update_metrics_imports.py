#!/usr/bin/env python3
"""
Script para atualizar os imports de pepperpy.core.common.metrics para pepperpy.core.metrics.
"""

import os
import re
from pathlib import Path


def update_imports_in_file(file_path):
    """
    Atualiza os imports no arquivo especificado.

    Args:
        file_path: Caminho para o arquivo a ser atualizado

    Returns:
        bool: True se o arquivo foi modificado, False caso contrário
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Padrão para encontrar imports do módulo antigo
    pattern = r"from pepperpy\.core\.common\.metrics(\..*?)? import (.*)"

    # Verifica se o padrão existe no conteúdo
    if not re.search(pattern, content):
        return False

    # Substitui os imports
    modified_content = re.sub(
        pattern, r"from pepperpy.core.metrics\1 import \2", content
    )

    # Escreve o conteúdo modificado de volta para o arquivo
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(modified_content)

    return True


def find_python_files(root_dir):
    """
    Encontra todos os arquivos Python no diretório especificado.

    Args:
        root_dir: Diretório raiz para iniciar a busca

    Returns:
        list: Lista de caminhos para arquivos Python
    """
    python_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def main():
    """Função principal."""
    # Diretório raiz do projeto
    root_dir = Path(__file__).parent

    # Encontra todos os arquivos Python
    python_files = find_python_files(root_dir)

    # Contador de arquivos modificados
    modified_count = 0

    # Atualiza os imports em cada arquivo
    for file_path in python_files:
        if update_imports_in_file(file_path):
            modified_count += 1
            print(f"Atualizado: {file_path}")

    print(f"\nTotal de arquivos atualizados: {modified_count}")


if __name__ == "__main__":
    main()
