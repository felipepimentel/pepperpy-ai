#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe no arquivo pepperpy/workflows/base.py.
"""

import re
from pathlib import Path


def fix_workflows_base_py():
    """Corrige erros de sintaxe no arquivo pepperpy/workflows/base.py."""
    file_path = Path("pepperpy/workflows/base.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Corrigir a indentação inesperada na linha 613
    content = re.sub(
        r'"""Initialize workflow\.\s+Args:\s+definition: Workflow definition\s+"""\s+super\(\)\.__init__\(definition\.name\)',
        '"""Initialize workflow.\n\n        Args:\n            definition: Workflow definition\n        """\n        super().__init__(definition.name)',
        content,
    )

    # Corrigir o erro de sintaxe na linha 726 (falta de dois pontos após return)
    content = re.sub(
        r'return {"step_id": step\.id, "action": step\.action, "status": "executed"}',
        'return {"step_id": step.id, "action": step.action, "status": "executed"}',
        content,
    )

    # Corrigir comentários que estão causando problemas de redefinição
    content = re.sub(
        r"# from pepperpy\.core\.components import ComponentState  # Removido: Redefinition of unused `ComponentState` from line 21",
        "# Removido: Redefinition of unused `ComponentState` from line 21",
        content,
    )

    content = re.sub(
        r"# from pepperpy\.core\.types\.enums import ComponentState  # Removido: Redefinition of unused `ComponentState` from line 23",
        "# Removido: Redefinition of unused `ComponentState` from line 23",
        content,
    )

    content = re.sub(
        r"#     def __init__\(self, definition: WorkflowDefinition\) -> None:  # Removido: Redefinition of unused `__init__` from line 511",
        "# Removido: Redefinition of unused `__init__` from line 511",
        content,
    )

    content = re.sub(
        r"#     def add_metadata\(self, key: str, value: Any\) -> None:  # Removido: Redefinition of unused `add_metadata` from line 545",
        "# Removido: Redefinition of unused `add_metadata` from line 545",
        content,
    )

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"Erros de sintaxe corrigidos em {file_path}")
    print("Correção de workflows/base.py concluída com sucesso!")


if __name__ == "__main__":
    fix_workflows_base_py()
