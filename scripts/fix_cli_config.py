#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe no arquivo cli/commands/config.py.
"""

import re
from pathlib import Path


def fix_cli_config():
    """Corrige erros de sintaxe no arquivo cli/commands/config.py."""
    file_path = Path("pepperpy/cli/commands/config.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return False

    try:
        content = file_path.read_text()

        # Corrigir o comando set
        pattern1 = r'@config\.command\(\)\s+@click\.argument\("key"\)\s+@click\.argument\("value"\)\s+"""Set a configuration value\.'
        replacement1 = '''@config.command()
@click.argument("key")
@click.argument("value")
def set(key: str, value: str) -> None:
    """Set a configuration value.'''

        # Corrigir o comando get
        pattern2 = r'@config\.command\(\)\s+@click\.argument\("key"\)\s+"""Get a configuration value\.'
        replacement2 = '''@config.command()
@click.argument("key")
def get(key: str) -> None:
    """Get a configuration value.'''

        # Corrigir o comando validate
        pattern3 = r'@config\.command\(\)\s+"""Validate current configuration\."""'
        replacement3 = '''@config.command()
def validate() -> None:
    """Validate current configuration."""'''

        # Aplicar as correções
        new_content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
        new_content = re.sub(pattern2, replacement2, new_content, flags=re.DOTALL)
        new_content = re.sub(pattern3, replacement3, new_content, flags=re.DOTALL)

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
    success = fix_cli_config()
    if success:
        print("Correção de cli/commands/config.py concluída com sucesso!")
    else:
        print("Não foi possível corrigir cli/commands/config.py.")


if __name__ == "__main__":
    main()
