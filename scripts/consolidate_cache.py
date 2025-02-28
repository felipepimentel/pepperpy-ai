#!/usr/bin/env python
"""
Script para consolidar o sistema de cache.
"""

import shutil
from pathlib import Path


def consolidate_cache_file(source_path, dest_path):
    """
    Consolida um arquivo de cache, movendo-o para o diretório de caching.

    Args:
        source_path: Caminho do arquivo de origem
        dest_path: Caminho do arquivo de destino
    """
    source_file = Path(source_path)
    dest_file = Path(dest_path)

    if not source_file.exists():
        print(f"Arquivo de origem não existe: {source_file}")
        return False

    # Criar diretório de destino se não existir
    dest_file.parent.mkdir(parents=True, exist_ok=True)

    # Copiar o arquivo
    shutil.copy2(source_file, dest_file)
    print(f"Copiado: {source_file} -> {dest_file}")

    # Criar stub de compatibilidade
    module_name = dest_file.stem
    with open(source_file, "w") as f:
        f.write(f'"""Compatibility stub for {module_name}"""\n\n')
        f.write(f"from pepperpy.caching.{module_name} import *  # noqa\n")

    print(f"Criado stub de compatibilidade em {source_file}")
    return True


def remove_redundant_file(file_path):
    """
    Remove um arquivo redundante.

    Args:
        file_path: Caminho do arquivo a ser removido
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"Arquivo não existe: {file_path}")
        return False

    # Fazer backup do arquivo antes de remover
    backup_dir = Path("backup/caching")
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_file = backup_dir / file_path.name
    shutil.copy2(file_path, backup_file)
    print(f"Backup criado: {file_path} -> {backup_file}")

    # Remover o arquivo
    file_path.unlink()
    print(f"Arquivo removido: {file_path}")
    return True


def main():
    """Função principal para consolidar o sistema de cache."""
    # Mover arquivos de cache para o diretório caching
    cache_files_to_move = [
        ("pepperpy/memory/cache.py", "pepperpy/caching/memory_cache.py"),
    ]

    # Remover arquivos redundantes
    redundant_files = [
        "pepperpy/caching/memory.py",
    ]

    # Mover arquivos de cache
    for source, dest in cache_files_to_move:
        print(f"\nMovendo {source} para {dest}...")
        if consolidate_cache_file(source, dest):
            print(f"Arquivo {source} consolidado com sucesso em {dest}")
        else:
            print(f"Falha ao consolidar arquivo {source}")

    # Remover arquivos redundantes
    for file_path in redundant_files:
        print(f"\nRemovendo arquivo redundante {file_path}...")
        if remove_redundant_file(file_path):
            print(f"Arquivo redundante {file_path} removido com sucesso")
        else:
            print(f"Falha ao remover arquivo redundante {file_path}")


if __name__ == "__main__":
    main()
