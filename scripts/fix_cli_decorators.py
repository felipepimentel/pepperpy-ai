#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe no arquivo cli/decorators.py
"""

import re
from pathlib import Path


def fix_cli_decorators():
    """
    Corrige erros de sintaxe no arquivo cli/decorators.py
    """
    file_path = Path("pepperpy/cli/decorators.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado!")
        return False

    try:
        content = file_path.read_text()

        # Corrigir a função command()
        if "def command()" in content:
            # Corrigir a definição da função command
            content = re.sub(
                r"def command\(\)\s+name: str,\s+description: str,\s+group: str = \"default\",\s+aliases: Optional\[List\[str\]\] = None,\s+options: Optional\[Dict\[str, Any\]\] = None,\s+\) -> Callable\[\[F\], F\]:",
                'def command(\n    name: str,\n    description: str,\n    group: str = "default",\n    aliases: Optional[List[str]] = None,\n    options: Optional[Dict[str, Any]] = None,\n) -> Callable[[F], F]:',
                content,
            )

            # Corrigir a chamada para CommandDecorator
            content = re.sub(
                r"return CommandDecorator\(\)\s+name=name,\s+description=description,\s+group=group,\s+aliases=aliases,\s+options=options,\s+\)",
                "return CommandDecorator(\n        name=name,\n        description=description,\n        group=group,\n        aliases=aliases,\n        options=options,\n    )",
                content,
            )

        # Corrigir a função log_command_result
        if (
            "success=result," in content
            and 'message="Command succeeded" if result else "Command failed",'
            in content
        ):
            content = re.sub(
                r"logger\.info\(\s+success=result,\s+message=\"Command succeeded\" if result else \"Command failed\",\s+\)",
                'logger.info(\n                success=result,\n                message="Command succeeded" if result else "Command failed"\n            )',
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
    success = fix_cli_decorators()
    if success:
        print("Correção de cli/decorators.py concluída com sucesso!")
    else:
        print("Falha ao corrigir cli/decorators.py")
