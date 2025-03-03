#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe no arquivo cli/registry.py
"""

import re
from pathlib import Path


def fix_cli_registry():
    """
    Corrige erros de sintaxe no arquivo cli/registry.py
    """
    file_path = Path("pepperpy/cli/registry.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado!")
        return False

    try:
        content = file_path.read_text()

        # Corrigir a função register_command
        if "def register_command()" in content:
            # Corrigir a definição da função register_command
            content = re.sub(
                r"def register_command\(\)\s+self,\s+group_name: str,\s+command: Command,\s+aliases: Optional\[List\[str\]\] = None,\s+\) -> None:",
                "def register_command(\n        self,\n        group_name: str,\n        command: Command,\n        aliases: Optional[List[str]] = None,\n    ) -> None:",
                content,
            )

            # Corrigir o logger.info com extra
            content = re.sub(
                r"logger\.info\(\s+\"Registered command\",\s+extra=\{\}\s+\"group\": group_name,\s+\"command\": command\.name,\s+\"aliases\": aliases,\s+\},\s+\)",
                'logger.info(\n                "Registered command",\n                extra={\n                    "group": group_name,\n                    "command": command.name,\n                    "aliases": aliases,\n                },\n            )',
                content,
            )

            # Corrigir o raise CLIError com from e
            content = re.sub(
                r"raise CLIError\( from e\)\s+f\"Failed to register command \{command\.name\}: \{e\}\",\s+details=\{\}\s+\"group\": group_name,\s+\"command\": command\.name,\s+\"aliases\": aliases,\s+\"error\": str\(e\),\s+\},\s+\)",
                'raise CLIError(\n                f"Failed to register command {command.name}: {e}",\n                details={\n                    "group": group_name,\n                    "command": command.name,\n                    "aliases": aliases,\n                    "error": str(e),\n                },\n            ) from e',
                content,
            )

        # Escrever o conteúdo corrigido de volta ao arquivo
        file_path.write_text(content)
        print(f"Erros de sintaxe corrigidos em {file_path}")
        return True

    except Exception as e:
        print(f"Erro ao corrigir {file_path}: {e}")
        return False


if __name__ == "__main__":
    success = fix_cli_registry()
    if success:
        print("Correção de cli/registry.py concluída com sucesso!")
    else:
        print("Falha ao corrigir cli/registry.py")
