#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe no arquivo pepperpy/core/resources/base.py.
"""

from pathlib import Path


def fix_resources_base_py():
    """Corrige erros de sintaxe no arquivo pepperpy/core/resources/base.py."""
    file_path = Path("pepperpy/core/resources/base.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Corrigir a indentação da enumeração ResourceType
    for i in range(len(lines)):
        if 'FILE = "file"' in lines[i]:
            # Encontramos a linha com FILE = "file"
            # Vamos corrigir a indentação das linhas seguintes
            j = i + 1
            while j < len(lines) and any(
                resource in lines[j]
                for resource in [
                    "MEMORY",
                    "NETWORK",
                    "DATABASE",
                    "CACHE",
                    "ASSET",
                    "CUSTOM",
                ]
            ):
                # Remover a indentação extra
                lines[j] = lines[j].lstrip()
                j += 1

    # Corrigir a declaração da classe BaseResource
    for i in range(len(lines)):
        if "class BaseResource(ComponentBase, Resource):" in lines[i]:
            # Encontramos a declaração da classe
            # Verificar se a próxima linha tem a indentação correta para o docstring
            if (
                i + 1 < len(lines)
                and '"""Base resource implementation.' in lines[i + 1]
                and not lines[i + 1].startswith("    ")
            ):
                lines[i + 1] = "    " + lines[i + 1]

                # Também corrigir a próxima linha se for parte do docstring
                if (
                    i + 2 < len(lines)
                    and "This class provides a base implementation for resources."
                    in lines[i + 2]
                    and not lines[i + 2].startswith("    ")
                ):
                    lines[i + 2] = "    " + lines[i + 2]

                # E a linha de fechamento do docstring, se necessário
                if (
                    i + 3 < len(lines)
                    and '"""' in lines[i + 3]
                    and not lines[i + 3].startswith("    ")
                ):
                    lines[i + 3] = "    " + lines[i + 3]

    # Escrever o arquivo corrigido
    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(lines)

    print(f"Erros de sintaxe corrigidos em {file_path}")
    print("Correção de core/resources/base.py concluída com sucesso!")


if __name__ == "__main__":
    fix_resources_base_py()
