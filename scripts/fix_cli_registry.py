#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe no arquivo cli/registry.py.
"""

import re
from pathlib import Path


def fix_cli_registry():
    """Corrige erros de sintaxe no arquivo cli/registry.py."""
    file_path = Path("pepperpy/cli/registry.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return False

    try:
        content = file_path.read_text()

        # Corrigir o erro de sintaxe no logger.info()
        pattern = r'logger\.info\(\)\s+("Registered command",)\s+extra=\{\}\s+"group": group_name,\s+"command": command\.name,\s+"aliases": aliases,\s+\},'
        replacement = """logger.info(
                "Registered command",
                extra={
                    "group": group_name,
                    "command": command.name,
                    "aliases": aliases,
                },
            )"""

        # Aplicar a correção
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        # Verificar se houve alterações
        if new_content != content:
            file_path.write_text(new_content)
            print(f"Erros de sintaxe corrigidos em {file_path}")
            return True
        print(f"Nenhuma alteração necessária em {file_path}")
        return False

    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")
        return False


def main():
    """Função principal."""
    success = fix_cli_registry()
    if success:
        print("Correção de cli/registry.py concluída com sucesso!")
    else:
        print("Não foi possível corrigir cli/registry.py.")


if __name__ == "__main__":
    main()
