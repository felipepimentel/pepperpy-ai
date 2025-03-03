#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe no arquivo cli/base.py
"""

import re
from pathlib import Path


def fix_cli_base_py():
    """Corrige erros de sintaxe no arquivo cli/base.py"""
    file_path = Path("pepperpy/cli/base.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado!")
        return False

    try:
        content = file_path.read_text(encoding="utf-8")

        # Corrigir o método execute_subcommand
        # Problema: Parênteses e indentação incorretos em CommandResult()
        pattern_execute_subcommand = re.compile(
            r'if not subcommand:\s+return CommandResult\(\)\s+success=False,\s+message=f"Unknown subcommand: {subcommand_name}",\s+error=\{\}\s+"type": "unknown_subcommand",\s+"name": subcommand_name,\s+"available": list\(self\._commands\.keys\(\)\),\s+\},\s+\)'
        )
        replacement_execute_subcommand = (
            "if not subcommand:\n"
            "            return CommandResult(\n"
            "                success=False,\n"
            '                message=f"Unknown subcommand: {subcommand_name}",\n'
            "                error={\n"
            '                    "type": "unknown_subcommand",\n'
            '                    "name": subcommand_name,\n'
            '                    "available": list(self._commands.keys()),\n'
            "                },\n"
            "            )"
        )
        content = pattern_execute_subcommand.sub(
            replacement_execute_subcommand, content
        )

        # Corrigir o problema com CommandContext()
        pattern_subcontext = re.compile(
            r"subcontext = CommandContext\(\)\s+args=context\.args\[1:\],\s+options=context\.options,\s+env=context\.env,\s+config=context\.config,\s+\)"
        )
        replacement_subcontext = (
            "subcontext = CommandContext(\n"
            "            args=context.args[1:],\n"
            "            options=context.options,\n"
            "            env=context.env,\n"
            "            config=context.config,\n"
            "        )"
        )
        content = pattern_subcontext.sub(replacement_subcontext, content)

        # Corrigir o problema com CLIError
        pattern_cli_error = re.compile(
            r'raise CLIError\( from e\)\s+f"Failed to execute {subcommand\.name}: {e}",\s+details=\{\}\s+"command": subcommand\.name,\s+"error": str\(e\),\s+"error_type": type\(e\).__name__,\s+\},\s+\)'
        )
        replacement_cli_error = (
            "raise CLIError(\n"
            '                f"Failed to execute {subcommand.name}: {e}",\n'
            "                details={\n"
            '                    "command": subcommand.name,\n'
            '                    "error": str(e),\n'
            '                    "error_type": type(e).__name__,\n'
            "                },\n"
            "            ) from e"
        )
        content = pattern_cli_error.sub(replacement_cli_error, content)

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
