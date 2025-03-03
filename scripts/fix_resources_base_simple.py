#!/usr/bin/env python3
"""
Script simples para corrigir erros de sintaxe no arquivo pepperpy/core/resources/base.py.
"""

import os
import re


def fix_resources_base_py():
    """Corrige erros de sintaxe no arquivo pepperpy/core/resources/base.py."""
    file_path = "pepperpy/core/resources/base.py"

    if not os.path.exists(file_path):
        print(f"Arquivo {file_path} não encontrado.")
        return

    # Ler o conteúdo do arquivo
    with open(file_path, encoding="utf-8") as file:
        content = file.read()

    # Corrigir a indentação da enumeração ResourceType
    # Procurar por padrões como '    MEMORY = "memory"' e remover a indentação extra
    content = re.sub(
        r'(\s+)(MEMORY|NETWORK|DATABASE|CACHE|ASSET|CUSTOM)\s+=\s+"', r'\2 = "', content,
    )

    # Corrigir a declaração da classe BaseResource
    # Adicionar indentação ao docstring da classe
    content = re.sub(
        r'class BaseResource\(ComponentBase, Resource\):\n("""Base resource implementation)',
        r"class BaseResource(ComponentBase, Resource):\n    \1",
        content,
    )

    # Corrigir a indentação das linhas seguintes do docstring
    content = re.sub(
        r'(    """Base resource implementation.)\n(This class provides)',
        r"\1\n    \2",
        content,
    )

    # Corrigir a indentação da linha de fechamento do docstring
    content = re.sub(
        r'(    This class provides a base implementation for resources.)\n(""")',
        r"\1\n    \2",
        content,
    )

    # Escrever o conteúdo corrigido de volta ao arquivo
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"Erros de sintaxe corrigidos em {file_path}")
    print("Correção de core/resources/base.py concluída com sucesso!")


if __name__ == "__main__":
    fix_resources_base_py()
