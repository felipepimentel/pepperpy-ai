#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe em pepperpy/workflows/base.py
"""

import re
from pathlib import Path


def fix_workflows_base_py():
    """Corrige erros de sintaxe em pepperpy/workflows/base.py."""
    file_path = Path("pepperpy/workflows/base.py")
    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return False

    # Ler o conteúdo original
    with open(file_path, "r") as f:
        content = f.read()

    # Corrigir a indentação inesperada
    content = re.sub(
        r'"""\s+\s+super\(\)\.__init__\(definition\.name\)',
        '"""\n        super().__init__(definition.name)',
        content,
    )

    # Corrigir o ponto e vírgula desnecessário
    content = re.sub(
        r'return \{"step_id": step\.id, "action": step\.action, "status": "executed"\};',
        'return {"step_id": step.id, "action": step.action, "status": "executed"}',
        content,
    )

    # Escrever o conteúdo corrigido
    with open(file_path, "w") as f:
        f.write(content)

    print(f"Erros de sintaxe corrigidos em {file_path}")
    return True


if __name__ == "__main__":
    fix_workflows_base_py()
