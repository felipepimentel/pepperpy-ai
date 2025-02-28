#!/usr/bin/env python
"""
Script para mover os módulos audio, vision e multimodal para o diretório capabilities.
"""

import shutil
from pathlib import Path


def move_module(source_dir, dest_dir):
    """
    Move um módulo de origem para destino, criando diretórios se necessário.

    Args:
        source_dir: Diretório de origem
        dest_dir: Diretório de destino
    """
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)

    if not source_path.exists():
        print(f"Diretório de origem não existe: {source_path}")
        return False

    # Criar diretório de destino se não existir
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Se o destino já existir, mover arquivos individualmente
    if dest_path.exists():
        print(f"Destino já existe: {dest_path}, movendo arquivos individualmente")
        for item in source_path.glob("*"):
            dest_item = dest_path / item.name
            if item.is_file():
                if not dest_item.exists():
                    shutil.copy2(item, dest_item)
                    print(f"Copiado: {item} -> {dest_item}")
            elif item.is_dir():
                if not dest_item.exists():
                    shutil.copytree(item, dest_item)
                    print(f"Copiado diretório: {item} -> {dest_item}")
    else:
        # Caso contrário, mover o diretório inteiro
        shutil.copytree(source_path, dest_path)
        print(f"Copiado diretório: {source_path} -> {dest_path}")

    # Criar stub de compatibilidade
    module_name = source_path.name
    with open(source_path / "__init__.py", "w") as f:
        f.write(f'"""Compatibility stub for {module_name}"""\n\n')
        f.write(f"from pepperpy.capabilities.{module_name} import *  # noqa\n")

    print(f"Criado stub de compatibilidade em {source_path}/__init__.py")
    return True


def main():
    """Função principal para mover os módulos."""
    modules_to_move = [
        ("pepperpy/audio", "pepperpy/capabilities/audio"),
        ("pepperpy/vision", "pepperpy/capabilities/vision"),
        ("pepperpy/multimodal", "pepperpy/capabilities/multimodal"),
    ]

    for source, dest in modules_to_move:
        print(f"\nMovendo {source} para {dest}...")
        if move_module(source, dest):
            print(f"Módulo {source} movido com sucesso para {dest}")
        else:
            print(f"Falha ao mover módulo {source}")


if __name__ == "__main__":
    main()
