#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe no arquivo pepperpy/cli/base.py
"""

from pathlib import Path
import re


def fix_cli_base_py():
    """Corrige erros de sintaxe no arquivo pepperpy/cli/base.py"""
    file_path = Path("pepperpy/cli/base.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado!")
        return False

    try:
        content = file_path.read_text(encoding="utf-8")

        # Corrigir o método add_command
        pattern_add_command = re.compile(
            r"def add_command\(\)\s+self, command: Command, aliases: Optional\[List\[str\]\] = None\s+\) -> None:",
        )
        replacement_add_command = (
            "def add_command(\n"
            "        self, command: Command, aliases: Optional[List[str]] = None\n"
            "    ) -> None:"
        )
        content = pattern_add_command.sub(replacement_add_command, content)

        # Corrigir o erro de CLIError()
        pattern_cli_error = re.compile(
            r'raise CLIError\(\)\s+f"Command {command\.name} already exists in group {self\.name}"\s+\)',
        )
        replacement_cli_error = (
            'raise CLIError(\n'
            '                f"Command {command.name} already exists in group {self.name}"\n'
            '            )'
        )
        content = pattern_cli_error.sub(replacement_cli_error, content)

        # Corrigir o erro de CommandResult()
        pattern_command_result = re.compile(
            r'return CommandResult\(\)\s+success=False,\s+message=f"Missing subcommand for {self\.name}",\s+error=\{"type": "missing_subcommand"\},\s+\)',
        )
        replacement_command_result = (
            'return CommandResult(\n'
            '                success=False,\n'
            '                message=f"Missing subcommand for {self.name}",\n'
            '                error={"type": "missing_subcommand"},\n'
            '            )'
        )
        content = pattern_command_result.sub(replacement_command_result, content)

        # Escrever o conteúdo corrigido de volta ao arquivo
        file_path.write_text(content, encoding="utf-8")
        print(f"Erros de sintaxe corrigidos em {file_path}")
        return True

    except Exception as e:
        print(f"Erro ao corrigir {file_path}: {e}")
        return False


if __name__ == "__main__":
    if fix_cli_base_py():
        print("Correção de cli/base.py concluída com sucesso!")
    else:
        print("Falha ao corrigir cli/base.py")
