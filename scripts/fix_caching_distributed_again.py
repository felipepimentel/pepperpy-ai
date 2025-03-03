#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe no arquivo pepperpy/caching/distributed.py
"""

import re
from pathlib import Path


def fix_caching_distributed_py():
    """Corrige erros de sintaxe no arquivo pepperpy/caching/distributed.py"""
    file_path = Path("pepperpy/caching/distributed.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado!")
        return False

    try:
        content = file_path.read_text(encoding="utf-8")

        # Corrigir o método set
        pattern_set = re.compile(
            r"async def set\(\)\s+self, key: str, value: T, ttl: Optional\[Union\[int, timedelta\]\] = None\s+\) -> None:"
        )
        replacement_set = (
            "async def set(\n"
            "        self, key: str, value: T, ttl: Optional[Union[int, timedelta]] = None\n"
            "    ) -> None:"
        )
        content = pattern_set.sub(replacement_set, content)

        # Corrigir o método json.dumps()
        pattern_json_dumps = re.compile(
            r'json_message = json\.dumps\(\)\s+\{\}\s+"_serialized": True,\s+"data": serialized\.hex\(\),\s+\},\s+\)'
        )
        replacement_json_dumps = (
            "json_message = json.dumps({\n"
            '                    "_serialized": True,\n'
            '                    "data": serialized.hex(),\n'
            "                })"
        )
        content = pattern_json_dumps.sub(replacement_json_dumps, content)

        # Corrigir o bloco try/except
        pattern_try_except = re.compile(
            r'try:\s+# Serialize message if needed\s+if isinstance\(message, \(dict, list\)\):\s+json_message = json\.dumps\(message\)\s+elif hasattr\(message, "__bytes__"\):\s+serialized = self\.serializer\.serialize\(message\)\s+json_message = json\.dumps\(\)\s+\{\}\s+"_serialized": True,\s+"data": serialized\.hex\(\),\s+\},\s+\)\s+# Publish to channel\s+return self\._client\.publish\(channel, json_message\)\s+except Exception as e:'
        )
        replacement_try_except = (
            "try:\n"
            "            # Serialize message if needed\n"
            "            if isinstance(message, (dict, list)):\n"
            "                json_message = json.dumps(message)\n"
            '            elif hasattr(message, "__bytes__"):\n'
            "                serialized = self.serializer.serialize(message)\n"
            "                json_message = json.dumps({\n"
            '                    "_serialized": True,\n'
            '                    "data": serialized.hex(),\n'
            "                })\n"
            "            \n"
            "            # Publish to channel\n"
            "            return self._client.publish(channel, json_message)\n"
            "        except Exception as e:"
        )
        content = pattern_try_except.sub(replacement_try_except, content)

        # Escrever o conteúdo corrigido de volta ao arquivo
        file_path.write_text(content, encoding="utf-8")
        print(f"Erros de sintaxe corrigidos em {file_path}")
        return True

    except Exception as e:
        print(f"Erro ao corrigir {file_path}: {e}")
        return False


if __name__ == "__main__":
    if fix_caching_distributed_py():
        print("Correção de caching/distributed.py concluída com sucesso!")
    else:
        print("Falha ao corrigir caching/distributed.py")
