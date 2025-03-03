#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe no arquivo cli/commands/tool.py.
"""

import re
from pathlib import Path


def fix_cli_tool():
    """Corrige erros de sintaxe no arquivo cli/commands/tool.py."""
    file_path = Path("pepperpy/cli/commands/tool.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return False

    try:
        content = file_path.read_text()

        # Corrigir o comando create
        pattern1 = r'@tool\.command\(\)\s+@click\.argument\("name"\)\s+@click\.option\("--type", help="Tool type"\)\s+@click\.option\("--config", type=click\.Path\(exists=True\), help="Tool configuration file"\)\s+"""Create a new tool\.'
        replacement1 = '''@tool.command()
@click.argument("name")
@click.option("--type", help="Tool type")
@click.option("--config", type=click.Path(exists=True), help="Tool configuration file")
def create(name: str, type: Optional[str] = None, config: Optional[str] = None) -> None:
    """Create a new tool.'''

        # Corrigir o comando list
        pattern2 = r'@tool\.command\(\)\s+@click\.option\("--type", help="Filter by tool type"\)\s+@click\.option\("--status", help="Filter by status"\)\s+"""List available tools\."""'
        replacement2 = '''@tool.command()
@click.option("--type", help="Filter by tool type")
@click.option("--status", help="Filter by status")
def list(type: Optional[str] = None, status: Optional[str] = None) -> None:
    """List available tools."""'''

        # Corrigir o comando run
        pattern3 = r'@tool\.command\(\)\s+@click\.argument\("name"\)\s+@click\.argument\("operation"\)\s+@click\.option\("--input", type=click\.Path\(exists=True\), help="Input file"\)\s+@click\.option\("--output", type=click\.Path\(\), help="Output file"\)\s+"""Run a tool operation\.'
        replacement3 = '''@tool.command()
@click.argument("name")
@click.argument("operation")
@click.option("--input", type=click.Path(exists=True), help="Input file")
@click.option("--output", type=click.Path(), help="Output file")
def run(name: str, operation: str, input: Optional[str] = None, output: Optional[str] = None) -> None:
    """Run a tool operation.'''

        # Aplicar as correções
        new_content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
        new_content = re.sub(pattern2, replacement2, new_content, flags=re.DOTALL)
        new_content = re.sub(pattern3, replacement3, new_content, flags=re.DOTALL)

        # Adicionar o import Optional se não existir
        if "from typing import Optional" not in new_content:
            new_content = re.sub(
                r"import click",
                "import click\nfrom typing import Optional",
                new_content,
            )

        # Verificar se houve alterações
        if new_content != content:
            file_path.write_text(new_content)
            print(f"Erros de sintaxe corrigidos em {file_path}")
            return True
        else:
            print(f"Nenhuma alteração necessária em {file_path}")
            return False

    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")
        return False


def main():
    """Função principal."""
    success = fix_cli_tool()
    if success:
        print("Correção de cli/commands/tool.py concluída com sucesso!")
    else:
        print("Não foi possível corrigir cli/commands/tool.py.")


if __name__ == "__main__":
    main()
