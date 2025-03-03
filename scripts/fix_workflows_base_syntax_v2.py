#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe no arquivo pepperpy/workflows/base.py.
"""

from pathlib import Path


def fix_workflows_base_py():
    """Corrige erros de sintaxe no arquivo pepperpy/workflows/base.py."""
    file_path = Path("pepperpy/workflows/base.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return

    with open(file_path, encoding="utf-8") as file:
        lines = file.readlines()

    # Corrigir o problema de indentação na linha 613
    # Encontrar a seção problemática
    start_line = 0
    end_line = 0
    for i, line in enumerate(lines):
        if "# Removido: Redefinition of unused `__init__` from line 511" in line:
            start_line = i
        if start_line > 0 and "self.results: Dict[str, Any] = {}" in line:
            end_line = i
            break

    if start_line > 0 and end_line > 0:
        # Reescrever a seção com a indentação correta
        new_section = [
            "# Removido: Redefinition of unused `__init__` from line 511\n",
            "    def __init__(self, definition: WorkflowDefinition) -> None:\n",
            '        """Initialize workflow.\n',
            "\n",
            "        Args:\n",
            "            definition: Workflow definition\n",
            '        """\n',
            "        super().__init__(definition.name)\n",
            "        self.definition = definition\n",
            "        self.state: Dict[str, Any] = {}\n",
            "        self.results: Dict[str, Any] = {}\n",
        ]

        # Substituir as linhas
        lines[start_line : end_line + 1] = new_section

    # Corrigir o problema na linha 726
    for i, line in enumerate(lines):
        if (
            'return {"step_id": step.id, "action": step.action, "status": "executed"}'
            in line
        ):
            # Adicionar dois pontos no final da linha se necessário
            if not line.strip().endswith(":"):
                lines[i] = line.rstrip() + "\n"

    # Escrever o arquivo corrigido
    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(lines)

    print(f"Erros de sintaxe corrigidos em {file_path}")
    print("Correção de workflows/base.py concluída com sucesso!")


if __name__ == "__main__":
    fix_workflows_base_py()
