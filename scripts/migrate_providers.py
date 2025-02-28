#!/usr/bin/env python3
"""
Script para migrar providers distribuídos para o diretório centralizado.

Este script automatiza o processo de padronização dos providers no framework PepperPy,
movendo os providers distribuídos em seus respectivos módulos de domínio para o
diretório centralizado `pepperpy/providers/`.
"""

import shutil
from pathlib import Path

# Configuração
PEPPERPY_ROOT = Path(__file__).parent.parent / "pepperpy"
PROVIDERS_ROOT = PEPPERPY_ROOT / "providers"
MIGRATION_MODULES = [
    ("embedding", "embedding"),
    ("memory", "memory"),
    ("rag", "rag"),
    ("cloud", "cloud"),
]

# Mensagem de aviso de depreciação
DEPRECATION_WARNING = """
\"\"\"
COMPATIBILITY STUB: This module has been moved to pepperpy.providers.{target_module}
This stub exists for backward compatibility and will be removed in a future version
\"\"\"

import warnings

warnings.warn(
    "The module pepperpy.{source_module}.providers has been moved to pepperpy.providers.{target_module}. "
    "Please update your imports. This compatibility stub will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

from pepperpy.providers.{target_module} import *
"""


def create_directory_if_not_exists(directory):
    """Cria um diretório se ele não existir."""
    if not directory.exists():
        print(f"Criando diretório: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def create_init_file(directory, content=""):
    """Cria um arquivo __init__.py em um diretório."""
    init_file = directory / "__init__.py"
    if not init_file.exists():
        print(f"Criando arquivo: {init_file}")
        with open(init_file, "w") as f:
            f.write(content)


def migrate_module(source_module, target_module):
    """Migra um módulo de providers para o diretório centralizado."""
    source_path = PEPPERPY_ROOT / source_module / "providers"
    target_path = PROVIDERS_ROOT / target_module

    if not source_path.exists():
        print(f"Módulo de origem não encontrado: {source_path}")
        return False

    # Criar diretório de destino
    create_directory_if_not_exists(target_path)
    create_init_file(target_path)

    # Copiar arquivos
    for item in source_path.glob("*"):
        if item.is_file():
            if item.name == "__init__.py":
                # Preservar o conteúdo original do __init__.py
                with open(item, "r") as f:
                    original_content = f.read()

                # Criar stub de compatibilidade
                with open(item, "w") as f:
                    f.write(
                        DEPRECATION_WARNING.format(
                            source_module=source_module, target_module=target_module
                        )
                    )

                # Copiar conteúdo original para o novo local
                with open(target_path / "__init__.py", "w") as f:
                    f.write(original_content)
            else:
                # Copiar arquivo para o novo local
                print(f"Copiando arquivo: {item} -> {target_path / item.name}")
                shutil.copy2(item, target_path / item.name)
        elif item.is_dir():
            # Copiar subdiretório recursivamente
            target_subdir = target_path / item.name
            print(f"Copiando diretório: {item} -> {target_subdir}")
            shutil.copytree(item, target_subdir, dirs_exist_ok=True)

    return True


def main():
    """Função principal do script."""
    print("Iniciando migração de providers...")

    # Verificar se o diretório providers existe
    create_directory_if_not_exists(PROVIDERS_ROOT)
    create_init_file(PROVIDERS_ROOT)

    # Migrar cada módulo
    for source_module, target_module in MIGRATION_MODULES:
        print(f"\nMigrando {source_module}/providers -> providers/{target_module}")
        if migrate_module(source_module, target_module):
            print(f"Migração de {source_module}/providers concluída com sucesso!")
        else:
            print(f"Falha na migração de {source_module}/providers.")

    print("\nMigração de providers concluída!")
    print(
        "Por favor, verifique os arquivos migrados e atualize as referências conforme necessário."
    )


if __name__ == "__main__":
    main()
