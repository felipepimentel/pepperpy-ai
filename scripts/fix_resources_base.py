#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe em pepperpy/core/resources/base.py
"""

import re
from pathlib import Path


def fix_resources_base_py():
    """Corrige erros de sintaxe em pepperpy/core/resources/base.py."""
    file_path = Path("pepperpy/core/resources/base.py")
    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return False

    # Ler o conteúdo original
    with open(file_path) as f:
        content = f.read()

    # Corrigir a indentação da enumeração ResourceType
    content = re.sub(
        r'FILE = "file"\s+\s+MEMORY = "memory"\s+\s+NETWORK = "network"\s+\s+DATABASE = "database"\s+\s+CLOUD = "cloud"\s+\s+CUSTOM = "custom"',
        'FILE = "file"\nMEMORY = "memory"\nNETWORK = "network"\nDATABASE = "database"\nCLOUD = "cloud"\nCUSTOM = "custom"',
        content,
    )

    # Corrigir a definição da classe BaseResource
    content = re.sub(
        r'class BaseResource\(ComponentBase, Resource\):\s+"""Base resource implementation\.',
        'class BaseResource(ComponentBase, Resource):\n    """Base resource implementation.',
        content,
    )

    # Escrever o conteúdo corrigido
    with open(file_path, "w") as f:
        f.write(content)

    print(f"Erros de sintaxe corrigidos em {file_path}")
    return True


if __name__ == "__main__":
    fix_resources_base_py()
