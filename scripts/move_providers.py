#!/usr/bin/env python
"""
Script para mover os provedores restantes para o diretório providers centralizado.
"""

import shutil
from pathlib import Path


def move_provider(source_dir, dest_dir):
    """
    Move um provedor de origem para destino, criando diretórios se necessário.

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
    parent_module = source_path.parent.name
    module_name = source_path.name
    with open(source_path / "__init__.py", "w") as f:
        f.write(f'"""Compatibility stub for {module_name}"""\n\n')
        f.write(f"from pepperpy.providers.{parent_module} import *  # noqa\n")

    print(f"Criado stub de compatibilidade em {source_path}/__init__.py")
    return True


def main():
    """Função principal para mover os provedores."""
    providers_to_move = [
        ("pepperpy/llm/providers", "pepperpy/providers/llm"),
        ("pepperpy/rag/providers", "pepperpy/providers/rag"),
        ("pepperpy/cloud/providers", "pepperpy/providers/cloud"),
    ]

    for source, dest in providers_to_move:
        print(f"\nMovendo {source} para {dest}...")
        if move_provider(source, dest):
            print(f"Provedor {source} movido com sucesso para {dest}")
        else:
            print(f"Falha ao mover provedor {source}")


if __name__ == "__main__":
    main()
