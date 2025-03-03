#!/usr/bin/env python3
"""
Script para corrigir erros de redefinição (F811) e variáveis não utilizadas (F841, B007).
"""

import re
import subprocess
from pathlib import Path


def fix_redefinitions(file_path, errors):
    """Corrige erros de redefinição e variáveis não utilizadas em um arquivo."""
    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return False

    try:
        content = file_path.read_text()
        lines = content.splitlines()
        modified = False

        # Ordenar erros por número de linha em ordem decrescente para evitar problemas com índices
        errors.sort(key=lambda x: x["line"], reverse=True)

        for error in errors:
            line_num = error["line"] - 1  # Ajustar para índice baseado em 0
            if line_num < 0 or line_num >= len(lines):
                continue

            line = lines[line_num]

            if error["code"] == "F811":  # Redefinição de variável não utilizada
                # Comentar a linha com a redefinição
                lines[line_num] = f"# {line}  # Removido: {error['message']}"
                modified = True
                print(f"Corrigido F811 na linha {error['line']} em {file_path}")

            elif error["code"] == "F841":  # Variável local atribuída mas não utilizada
                # Extrair o nome da variável da mensagem de erro
                var_match = re.search(r"Local variable `(\w+)`", error["message"])
                if var_match:
                    var_name = var_match.group(1)
                    # Comentar a linha com a atribuição
                    lines[line_num] = f"# {line}  # Removido: {error['message']}"
                    modified = True
                    print(f"Corrigido F841 na linha {error['line']} em {file_path}")

            elif error["code"] == "B007":  # Variável de controle de loop não utilizada
                # Extrair o nome da variável da mensagem de erro
                var_match = re.search(
                    r"Loop control variable `(\w+)`", error["message"],
                )
                if var_match:
                    var_name = var_match.group(1)
                    # Renomear a variável para _var_name
                    new_line = line.replace(var_name, f"_{var_name}")
                    lines[line_num] = new_line
                    modified = True
                    print(f"Corrigido B007 na linha {error['line']} em {file_path}")

        if modified:
            # Escrever o conteúdo modificado de volta ao arquivo
            file_path.write_text("\n".join(lines))
            return True

        return False

    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")
        return False


def parse_ruff_output(output):
    """Analisa a saída do comando ruff para extrair informações sobre os erros."""
    errors = []

    print(
        f"Analisando saída do ruff:\n{output[:500]}...",
    )  # Mostrar parte da saída para debug

    for line in output.splitlines():
        # Procurar por linhas que contêm erros F811, F841 ou B007
        match = re.search(r"pepperpy/(.+?):(\d+):(\d+): (F811|F841|B007) (.+)", line)
        if match:
            file_path, line_num, col, code, message = match.groups()
            errors.append({
                "file": f"pepperpy/{file_path}",
                "line": int(line_num),
                "column": int(col),
                "code": code,
                "message": message,
            })

    print(f"Encontrados {len(errors)} erros para corrigir")
    return errors


def main():
    """Função principal."""
    print("Iniciando correção de erros de redefinição e variáveis não utilizadas...")

    try:
        # Executar o comando ruff para obter os erros
        print("Executando ruff para identificar erros...")
        result = subprocess.run(
            ["ruff", "check", "pepperpy/", "--select=F811,F841,B007"],
            capture_output=True,
            text=True, check=False,
        )

        if result.returncode != 0:
            print("Erros encontrados pelo ruff.")
        else:
            print("Nenhum erro encontrado pelo ruff.")
            return

        # Analisar a saída para obter os erros
        errors = parse_ruff_output(result.stdout)

        if not errors:
            print("Nenhum erro para corrigir.")
            return

        # Agrupar erros por arquivo
        errors_by_file = {}
        for error in errors:
            file_path = error["file"]
            if file_path not in errors_by_file:
                errors_by_file[file_path] = []
            errors_by_file[file_path].append(error)

        print(f"Erros agrupados em {len(errors_by_file)} arquivos.")

        # Corrigir erros em cada arquivo
        files_fixed = 0
        for file_path, file_errors in errors_by_file.items():
            print(f"Processando {file_path} ({len(file_errors)} erros)...")
            if fix_redefinitions(Path(file_path), file_errors):
                files_fixed += 1

        print(f"\nTotal de arquivos corrigidos: {files_fixed}")

    except Exception as e:
        print(f"Erro ao executar o script: {e}")


if __name__ == "__main__":
    main()
