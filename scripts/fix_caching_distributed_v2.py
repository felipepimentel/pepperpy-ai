#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe no arquivo pepperpy/caching/distributed.py.
"""

import re
from pathlib import Path


def fix_caching_distributed_py():
    """Corrige erros de sintaxe no arquivo pepperpy/caching/distributed.py."""
    file_path = Path("pepperpy/caching/distributed.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return

    with open(file_path, encoding="utf-8") as file:
        content = file.read()

    # Corrigir parêntese extra na inicialização do Redis
    content = re.sub(
        r"retry_on_timeout=retry_on_timeout,\s+\)\s+\)",
        "retry_on_timeout=retry_on_timeout,\n            )",
        content,
    )

    # Corrigir o bloco de exceção ImportError
    content = re.sub(
        r'raise ImportError\(\s+"Redis package is required for RedisCache\. "\s+"Install it with \'pip install redis\'\."\s+\) from None\s+"Install it with: pip install redis"\s+\)',
        'raise ImportError(\n                "Redis package is required for RedisCache. "\n                "Install it with \'pip install redis\'."\n            ) from None',
        content,
    )

    # Corrigir o bloco json.dumps() com indentação incorreta
    content = re.sub(
        r'json_message = json\.dumps\(\)\s+\{\}\s+"_serialized": True,\s+"data": serialized\.hex\(\),\s+\}\s+\)',
        'json_message = json.dumps({\n                    "_serialized": True,\n                    "data": serialized.hex(),\n                })',
        content,
    )

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"Erros de sintaxe corrigidos em {file_path}")
    print("Correção de caching/distributed.py concluída com sucesso!")


if __name__ == "__main__":
    fix_caching_distributed_py()
