#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe no arquivo pepperpy/core/resources/base.py.
"""

from pathlib import Path
import re

def fix_resources_base_py():
    """Corrige erros de sintaxe no arquivo pepperpy/core/resources/base.py."""
    file_path = Path("pepperpy/core/resources/base.py")
    
    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return
    
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Corrigir a indentação da enumeração ResourceType
    content = re.sub(
        r'FILE = "file"\s+MEMORY = "memory"',
        'FILE = "file"\nMEMORY = "memory"',
        content
    )
    
    # Corrigir a declaração da classe BaseResource
    content = re.sub(
        r'class BaseResource\(ComponentBase, Resource\):\s+"""Base resource implementation\.',
        'class BaseResource(ComponentBase, Resource):\n    """Base resource implementation.',
        content
    )
    
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    
    print(f"Erros de sintaxe corrigidos em {file_path}")
    print(f"Correção de core/resources/base.py concluída com sucesso!")

if __name__ == "__main__":
    fix_resources_base_py() 