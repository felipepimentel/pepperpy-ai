#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe no arquivo cli/commands/workflow.py
"""

import re
from pathlib import Path


def fix_cli_workflow():
    """
    Corrige erros de sintaxe no arquivo cli/commands/workflow.py
    """
    file_path = Path("pepperpy/cli/commands/workflow.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado!")
        return False

    try:
        content = file_path.read_text()

        # Corrigir a função run com parâmetros incorretos
        if (
            '@click.option("--async", "is_async", is_flag=True, help="Run asynchronously")'
            in content
        ):
            # Encontrar o padrão da função run com erro
            pattern = r"@click\.option\(\"--async\", \"is_async\", is_flag=True, help=\"Run asynchronously\"\)\s+workflow_id: str, input_file: Optional\[str\] = None, is_async: bool = False\s+\) -> None:"
            replacement = '@click.option("--async", "is_async", is_flag=True, help="Run asynchronously")\ndef run(workflow_id: str, input_file: Optional[str] = None, is_async: bool = False) -> None:'
            content = re.sub(pattern, replacement, content)

        # Corrigir o comando list sem definição de função
        if "@workflow.command()" in content and '"""List workflows."""' in content:
            pattern = r"@workflow\.command\(\)\s+@click\.option\(\"--state\", type=click\.Choice\(\[s\.name for s in WorkflowState\]\)\)\s+\"\"\"List workflows\.\"\"\""
            replacement = '@workflow.command()\n@click.option("--state", type=click.Choice([s.name for s in WorkflowState]))\ndef list_workflows(state: Optional[str] = None) -> None:\n    """List workflows."""'
            content = re.sub(pattern, replacement, content)

        # Escrever o conteúdo corrigido de volta ao arquivo
        file_path.write_text(content)
        print(f"Erros de sintaxe corrigidos em {file_path}")
        return True

    except Exception as e:
        print(f"Erro ao corrigir {file_path}: {e}")
        return False


if __name__ == "__main__":
    success = fix_cli_workflow()
    if success:
        print("Correção de cli/commands/workflow.py concluída com sucesso!")
    else:
        print("Falha ao corrigir cli/commands/workflow.py")
