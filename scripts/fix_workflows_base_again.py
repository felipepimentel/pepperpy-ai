#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe no arquivo pepperpy/workflows/base.py
"""

import re
from pathlib import Path


def fix_workflows_base_py():
    """Corrige erros de sintaxe no arquivo pepperpy/workflows/base.py"""
    file_path = Path("pepperpy/workflows/base.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado!")
        return False

    try:
        content = file_path.read_text(encoding="utf-8")

        # Corrigir a indentação do método __init__ na classe WorkflowEngine
        pattern_init = re.compile(
            r'"""Workflow definition\s+Args:\s+definition: Workflow definition\s+"""\s+super\(\).__init__\(definition\.name\)'
        )
        replacement_init = (
            '"""Workflow definition\n'
            "        Args:\n"
            "            definition: Workflow definition\n"
            '        """\n'
            "        super().__init__(definition.name)"
        )
        content = pattern_init.sub(replacement_init, content)

        # Corrigir o ponto e vírgula no final do método execute_step
        pattern_execute_step = re.compile(
            r'return \{"step_id": step\.id, "action": step\.action, "status": "executed"\}'
        )
        replacement_execute_step = (
            'return {"step_id": step.id, "action": step.action, "status": "executed"}'
        )
        content = pattern_execute_step.sub(replacement_execute_step, content)

        # Escrever o conteúdo corrigido de volta ao arquivo
        file_path.write_text(content, encoding="utf-8")
        print(f"Erros de sintaxe corrigidos em {file_path}")
        return True

    except Exception as e:
        print(f"Erro ao corrigir {file_path}: {e}")
        return False


if __name__ == "__main__":
    if fix_workflows_base_py():
        print("Correção de workflows/base.py concluída com sucesso!")
    else:
        print("Falha ao corrigir workflows/base.py")
