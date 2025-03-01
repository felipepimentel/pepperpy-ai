#!/usr/bin/env python3
"""Script para completar a consolidação de providers."""
import os
import shutil
from pathlib import Path

# Diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent
PEPPERPY_ROOT = PROJECT_ROOT / "pepperpy"

def create_stub(original_path, new_path):
    """Cria um stub de compatibilidade."""
    original_path = Path(original_path)
    new_path = Path(new_path)
    # Determinar o caminho relativo para o import
    rel_path = os.path.relpath(new_path, original_path.parent)
    rel_path = rel_path.replace(".py", "").replace("/", ".")
    if rel_path.startswith(".."):
        # Converter para import absoluto
        parts = new_path.relative_to(PROJECT_ROOT).parts
        rel_path = ".".join(parts).replace(".py", "")

    # Criar o stub
    stub_content = f"""# DEPRECATED: Este módulo foi movido para {rel_path}
# Este stub será removido em uma versão futura.
