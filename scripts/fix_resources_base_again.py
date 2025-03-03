#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe no arquivo pepperpy/core/resources/base.py
"""

import re
from pathlib import Path


def fix_resources_base_py():
    """Corrige erros de sintaxe no arquivo pepperpy/core/resources/base.py"""
    file_path = Path("pepperpy/core/resources/base.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado!")
        return False

    try:
        content = file_path.read_text(encoding="utf-8")

        # Corrigir a indentação da enumeração ResourceType
        pattern_resource_type = re.compile(
            r'class ResourceType\(Enum\):\s+"""Resource type enumeration\."""\s+FILE = "file"\s+MEMORY = "memory"\s+NETWORK = "network"\s+DATABASE = "database"'
        )
        replacement_resource_type = (
            "class ResourceType(Enum):\n"
            '    """Resource type enumeration."""\n'
            '    FILE = "file"\n'
            '    MEMORY = "memory"\n'
            '    NETWORK = "network"\n'
            '    DATABASE = "database"'
        )
        content = pattern_resource_type.sub(replacement_resource_type, content)

        # Corrigir a definição da classe BaseResource
        pattern_base_resource = re.compile(
            r"class BaseResource\(ComponentBase, Resource\):"
        )
        replacement_base_resource = "class BaseResource(ComponentBase, Resource):"
        content = pattern_base_resource.sub(replacement_base_resource, content)

        # Escrever o conteúdo corrigido de volta ao arquivo
        file_path.write_text(content, encoding="utf-8")
        print(f"Erros de sintaxe corrigidos em {file_path}")
        return True

    except Exception as e:
        print(f"Erro ao corrigir {file_path}: {e}")
        return False


if __name__ == "__main__":
    if fix_resources_base_py():
        print("Correção de core/resources/base.py concluída com sucesso!")
    else:
        print("Falha ao corrigir core/resources/base.py")
