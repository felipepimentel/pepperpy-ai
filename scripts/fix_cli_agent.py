#!/usr/bin/env python3
"""
Script para corrigir erros de sintaxe no arquivo cli/commands/agent.py.
"""

import re
from pathlib import Path


def fix_cli_agent():
    """Corrige erros de sintaxe no arquivo cli/commands/agent.py."""
    file_path = Path("pepperpy/cli/commands/agent.py")

    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return False

    try:
        content = file_path.read_text()

        # Corrigir o erro de sintaxe no bloco de raise PepperpyError
        pattern1 = r'raise PepperpyError\(\)\s+message=f"Agent not found: \{agent_id\}",\s+details=\{"agent_id": agent_id\},\s+recovery_hint="Check agent ID and try again",\s+\)'
        replacement1 = """raise PepperpyError(
                message=f"Agent not found: {agent_id}",
                details={"agent_id": agent_id},
                recovery_hint="Check agent ID and try again",
            )"""

        # Corrigir o erro de sintaxe no bloco de raise PepperpyError com from e
        pattern2 = r'raise PepperpyError\( from e\)\s+message=f"Failed to update agent: \{e\}",\s+details=\{\}\s+"agent_id": agent_id,\s+"name": name,\s+"description": description,\s+\},\s+recovery_hint="Check agent configuration and try again",\s+\)'
        replacement2 = """raise PepperpyError(
            message=f"Failed to update agent: {e}",
            details={
                "agent_id": agent_id,
                "name": name,
                "description": description,
            },
            recovery_hint="Check agent configuration and try again",
        ) from e"""

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
    success = fix_cli_agent()
    if success:
        print("Correção de cli/commands/agent.py concluída com sucesso!")
    else:
        print("Não foi possível corrigir cli/commands/agent.py.")


if __name__ == "__main__":
    main()
