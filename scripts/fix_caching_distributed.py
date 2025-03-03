#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe no arquivo caching/distributed.py.
"""

from pathlib import Path
import re

def fix_caching_distributed():
    """Corrige erros de sintaxe no arquivo caching/distributed.py."""
    file_path = Path("pepperpy/caching/distributed.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return False

    try:
        content = file_path.read_text()

        # Corrigir o erro de sintaxe na inicialização do Redis.Redis()
        pattern1 = r"self\._client = redis\.Redis\(\)\s+host=host,\s+port=port,\s+db=db,\s+password=password,\s+socket_timeout=socket_timeout,\s+socket_connect_timeout=socket_connect_timeout,\s+retry_on_timeout=retry_on_timeout,"
        replacement1 = """self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                retry_on_timeout=retry_on_timeout,
            )"""

        # Corrigir o erro de sintaxe no raise ImportError
        pattern2 = r'raise ImportError\( from None\)\s+"Redis package is required for RedisCache\. "'
        replacement2 = """raise ImportError(
                "Redis package is required for RedisCache. "
                "Install it with 'pip install redis'."
            ) from None"""

        # Aplicar as correções
        new_content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
        new_content = re.sub(pattern2, replacement2, new_content, flags=re.DOTALL)

        # Verificar se houve alterações
        if new_content != content:
            file_path.write_text(new_content)
            print(f"Erros de sintaxe corrigidos em {file_path}")
            return True
        print(f"Nenhuma alteração necessária em {file_path}")
        return False

    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")
        return False

def main():
    """Função principal."""
    success = fix_caching_distributed()
    if success:
        print("Correção de caching/distributed.py concluída com sucesso!")
    else:
        print("Não foi possível corrigir caching/distributed.py.")

if __name__ == "__main__":
    main()
