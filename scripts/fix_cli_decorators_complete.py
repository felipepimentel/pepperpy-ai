#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe no arquivo cli/decorators.py de forma mais completa
"""

import re
from pathlib import Path


def fix_cli_decorators_complete():
    """
    Corrige todos os erros de sintaxe no arquivo cli/decorators.py
    """
    file_path = Path("pepperpy/cli/decorators.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado!")
        return False

    try:
        content = file_path.read_text()

        # Corrigir a função __init__ da classe CommandDecorator
        if "def __init__()" in content:
            content = re.sub(
                r"def __init__\(\)\s+self,\s+name: str,\s+description: str,\s+group: str,\s+aliases: Optional\[List\[str\]\] = None,\s+options: Optional\[Dict\[str, Any\]\] = None,\s+\) -> None:",
                "def __init__(\n        self,\n        name: str,\n        description: str,\n        group: str,\n        aliases: Optional[List[str]] = None,\n        options: Optional[Dict[str, Any]] = None,\n    ) -> None:",
                content,
            )

        # Corrigir a função command()
        if "def command(" in content:
            # Já corrigido pelo script anterior
            pass

        # Corrigir o raise CLIError com from e
        content = re.sub(
            r"raise CLIError\( from e\)\s+f\"Command execution failed: \{e\}\",\s+details=\{\}\s+\"command\": self\.name,\s+\"error\": str\(e\),\s+\"error_type\": type\(e\).__name__,\s+\},\s+\)",
            'raise CLIError(\n                f"Command execution failed: {e}",\n                details={\n                    "command": self.name,\n                    "error": str(e),\n                    "error_type": type(e).__name__,\n                },\n            ) from e',
            content,
        )

        # Corrigir o return CommandResult para bool
        content = re.sub(
            r"return CommandResult\(\)\s+success=result,\s+message=\"Command succeeded\" if result else \"Command failed\",\s+\)",
            'return CommandResult(\n                success=result,\n                message="Command succeeded" if result else "Command failed",\n            )',
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
    success = fix_cli_decorators_complete()
    if success:
        print("Correção completa de cli/decorators.py concluída com sucesso!")
    else:
        print("Falha ao corrigir cli/decorators.py")
