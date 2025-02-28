#!/usr/bin/env python
"""
Script para corrigir os stubs de compatibilidade após a reestruturação.
Este script remove arquivos extras dos diretórios que deveriam ser apenas stubs.
"""

import shutil
from pathlib import Path


def fix_stub(dir_path, import_path):
    """
    Transforma um diretório em um stub de compatibilidade.

    Args:
        dir_path: Caminho para o diretório a ser transformado
        import_path: Caminho de importação para o novo local
    """
    dir_path = Path(dir_path)

    if not dir_path.exists():
        print(f"Diretório {dir_path} não existe")
        return

    # Backup dos arquivos (opcional)
    backup_dir = Path("backup") / dir_path.name
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Mover todos os arquivos exceto __init__.py para backup
    for item in dir_path.glob("*"):
        if item.name != "__init__.py":
            if item.is_file():
                shutil.copy2(item, backup_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, backup_dir / item.name, dirs_exist_ok=True)

    # Remover todos os arquivos e diretórios exceto __init__.py
    for item in dir_path.glob("*"):
        if item.name != "__init__.py":
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    # Corrigir o __init__.py
    module_name = dir_path.name
    with open(dir_path / "__init__.py", "w") as f:
        f.write(f'"""Compatibility stub for {module_name}"""\n\n')
        f.write(f"from {import_path} import *  # noqa\n")

    print(f"Diretório {dir_path} transformado em stub de compatibilidade")


def main():
    """Corrige todos os stubs de compatibilidade."""
    # Lista de diretórios a serem corrigidos e seus novos caminhos de importação
    stubs_to_fix = [
        ("pepperpy/common/errors", "pepperpy.core.errors"),
        ("pepperpy/agents/workflows", "pepperpy.workflows"),
        ("pepperpy/agents/providers", "pepperpy.providers.agent"),
        ("pepperpy/audio/providers", "pepperpy.providers.audio"),
    ]

    # Cria diretório de backup
    Path("backup").mkdir(exist_ok=True)

    # Corrige cada stub
    for dir_path, import_path in stubs_to_fix:
        fix_stub(dir_path, import_path)

    print("Todos os stubs foram corrigidos!")


if __name__ == "__main__":
    main()
