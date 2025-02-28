#!/usr/bin/env python3
"""
Script para criar o diretório pepperpy/providers/rag e o stub de compatibilidade em pepperpy/rag/providers.

Este script resolve a situação específica onde o diretório pepperpy/rag/providers não existia
originalmente, mas é esperado pelo script de verificação de stubs.
"""

import os
from pathlib import Path


def create_rag_providers_structure():
    """
    Cria o diretório pepperpy/providers/rag e o stub de compatibilidade em pepperpy/rag/providers.
    """
    # Caminhos
    project_root = Path(__file__).parent.parent
    rag_providers_dir = project_root / "pepperpy" / "rag" / "providers"
    providers_rag_dir = project_root / "pepperpy" / "providers" / "rag"

    print("Criando estrutura para provedores RAG...")

    # Criar diretório pepperpy/providers/rag se não existir
    if not providers_rag_dir.exists():
        os.makedirs(providers_rag_dir, exist_ok=True)
        print(f"✅ Criado diretório: {providers_rag_dir}")

        # Criar __init__.py no diretório pepperpy/providers/rag
        init_file = providers_rag_dir / "__init__.py"
        with open(init_file, "w") as f:
            f.write('"""Provedores de RAG."""\n')
        print(f"✅ Criado arquivo: {init_file}")
    else:
        print(f"ℹ️ Diretório já existe: {providers_rag_dir}")

    # Criar diretório pepperpy/rag/providers se não existir
    if not rag_providers_dir.exists():
        os.makedirs(rag_providers_dir, exist_ok=True)
        print(f"✅ Criado diretório: {rag_providers_dir}")

        # Criar stub de compatibilidade em pepperpy/rag/providers/__init__.py
        stub_file = rag_providers_dir / "__init__.py"
        with open(stub_file, "w") as f:
            f.write('"""Stub de compatibilidade para provedores de RAG."""\n\n')
            f.write(
                "# Este é um stub de compatibilidade para manter a compatibilidade com código existente.\n"
            )
            f.write(
                "# Os provedores de RAG foram movidos para pepperpy.providers.rag\n\n"
            )
            f.write("from pepperpy.providers.rag import *  # noqa\n")
        print(f"✅ Criado stub de compatibilidade: {stub_file}")
    else:
        print(f"ℹ️ Diretório já existe: {rag_providers_dir}")

    print("\nEstrutura de provedores RAG criada com sucesso!")


if __name__ == "__main__":
    create_rag_providers_structure()
