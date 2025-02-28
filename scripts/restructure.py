#!/usr/bin/env python
"""
Script para reestruturação do projeto PepperPy.
Este script fornece funções para:
- Mover módulos e arquivos
- Atualizar imports
- Criar stubs de compatibilidade
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict

ROOT_DIR = Path(__file__).parent.parent
PEPPERPY_DIR = ROOT_DIR / "pepperpy"


def ensure_directory_exists(path: Path) -> None:
    """Garante que o diretório existe, criando-o se necessário."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def create_init_file(directory: Path, description: str = "") -> None:
    """Cria um arquivo __init__.py com uma descrição."""
    init_path = directory / "__init__.py"
    if not init_path.exists():
        with open(init_path, "w") as f:
            if description:
                f.write(f'"""{description}"""\n\n')


def move_module(source: Path, destination: Path, create_init: bool = True) -> None:
    """Move um módulo de origem para destino, criando diretórios se necessário."""
    if not source.exists():
        print(f"Aviso: Módulo de origem não existe: {source}")
        return

    # Garantir que o diretório de destino exista
    ensure_directory_exists(destination.parent)

    # Mover o módulo
    if source.is_dir():
        if destination.exists() and destination.is_dir():
            # Se o destino já existir, mover arquivos individuais
            for item in source.iterdir():
                dest_item = destination / item.name
                if item.is_file():
                    shutil.copy2(item, dest_item)
                elif item.is_dir():
                    move_module(item, dest_item)
        else:
            # Caso contrário, mover o diretório inteiro
            shutil.copytree(source, destination)
    elif source.is_file():
        shutil.copy2(source, destination)

    # Criar __init__.py se necessário
    if create_init and destination.is_dir():
        init_source = source / "__init__.py" if source.is_dir() else None
        if init_source and init_source.exists():
            with open(init_source, "r") as f:
                description = ""
                for line in f:
                    if line.strip().startswith('"""') or line.strip().startswith("'''"):
                        description = line.strip()
                        break
            create_init_file(destination, description.strip("\"\"\"'''"))
        else:
            create_init_file(destination)


def create_reexport_stub(original_path: Path, new_path: Path) -> None:
    """Cria um stub de re-exportação para manter compatibilidade."""
    if not original_path.exists():
        print(f"Aviso: Caminho original não existe: {original_path}")
        return

    if original_path.is_file():
        # Obter o nome do módulo
        module_name = original_path.stem
        parent_dir = original_path.parent

        # Obter o caminho relativo para o novo local
        rel_path = os.path.relpath(new_path, parent_dir)
        rel_path = rel_path.replace("/", ".")
        if rel_path.endswith(".py"):
            rel_path = rel_path[:-3]

        # Criar o stub
        with open(original_path, "w") as f:
            f.write(f'"""Compatibility stub for {module_name}"""\n\n')
            f.write(f"from {rel_path} import *  # noqa\n")

    elif original_path.is_dir():
        # Criar __init__.py para o diretório
        init_path = original_path / "__init__.py"

        # Obter o caminho relativo para o novo local
        rel_path = os.path.relpath(new_path, original_path)
        rel_path = rel_path.replace("/", ".")
        if rel_path.endswith(".py"):
            rel_path = rel_path[:-3]

        # Criar o stub
        with open(init_path, "w") as f:
            f.write(f'"""Compatibility stub for {original_path.name}"""\n\n')
            f.write(f"from {rel_path} import *  # noqa\n")


def update_imports_in_file(file_path: Path, import_mappings: Dict[str, str]) -> None:
    """Atualiza os imports em um arquivo com base no mapeamento fornecido."""
    if not file_path.exists() or not file_path.is_file():
        return

    with open(file_path, "r") as f:
        content = f.read()

    for old_import, new_import in import_mappings.items():
        # Padrão para imports simples (import x.y.z)
        content = re.sub(
            rf"import\s+{re.escape(old_import)}(\s|$|\n|;)",
            f"import {new_import}\\1",
            content,
        )

        # Padrão para imports from (from x.y.z import a, b, c)
        content = re.sub(
            rf"from\s+{re.escape(old_import)}(\s+import)",
            f"from {new_import}\\1",
            content,
        )

    with open(file_path, "w") as f:
        f.write(content)


def update_imports_in_project(import_mappings: Dict[str, str]) -> None:
    """Atualiza todos os imports no projeto com base no mapeamento fornecido."""
    for root, _, files in os.walk(PEPPERPY_DIR):
        for file in files:
            if file.endswith(".py"):
                update_imports_in_file(Path(root) / file, import_mappings)


def main():
    print("Script de reestruturação do PepperPy")
    print("Execute as funções específicas para realizar a reestruturação")


if __name__ == "__main__":
    main()
