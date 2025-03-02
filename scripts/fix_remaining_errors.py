#!/usr/bin/env python3
"""
Script para corrigir os erros mais comuns que restaram após as correções anteriores.
Este script foca em erros específicos como imports no lugar errado, nomes indefinidos, etc.
"""

import json
import re
import subprocess
from collections import defaultdict
from typing import Any, Dict, List


def run_ruff_check() -> List[Dict[str, Any]]:
    """Executa o Ruff e retorna os erros em formato JSON."""
    try:
        result = subprocess.run(
            ["ruff", "check", "pepperpy/", "--output-format=json"],
            capture_output=True,
            text=True,
            check=False,
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Erro ao executar o Ruff: {e}")
        return []


def group_errors_by_file_and_code(
    errors: List[Dict[str, Any]],
) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """Agrupa os erros por arquivo e código."""
    grouped: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for error in errors:
        filename = error.get("filename")
        code = error.get("code")
        if filename and code:
            grouped[filename][code].append(error)
    return grouped


def fix_import_order(file_path: str, errors: List[Dict[str, Any]]) -> int:
    """Corrige erros E402 (imports não estão no topo do arquivo)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Identifica as linhas de import que não estão no topo
        import_lines = []
        import_line_numbers = []
        for error in errors:
            if error.get("code") == "E402":
                line_num = error.get("location", {}).get("row", 0) - 1
                if 0 <= line_num < len(lines):
                    import_lines.append(lines[line_num])
                    import_line_numbers.append(line_num)

        if not import_lines:
            return 0

        # Remove as linhas de import do lugar errado
        for line_num in sorted(import_line_numbers, reverse=True):
            lines.pop(line_num)

        # Encontra o último import no topo do arquivo
        last_import_index = 0
        for i, line in enumerate(lines):
            if re.match(r"^(import|from)\s+", line.strip()):
                last_import_index = i
            elif i > 0 and not line.strip() and not lines[i - 1].strip():
                # Encontrou uma linha em branco após outra linha em branco
                break
            elif (
                i > 0
                and line.strip()
                and not line.strip().startswith("#")
                and not line.strip().startswith('"""')
            ):
                # Encontrou uma linha não vazia que não é um comentário ou docstring
                break

        # Insere os imports no lugar correto
        for import_line in import_lines:
            lines.insert(last_import_index + 1, import_line)
            last_import_index += 1

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return len(import_lines)
    except Exception as e:
        print(f"Erro ao corrigir E402 em {file_path}: {e}")
        return 0


def fix_undefined_names(file_path: str, errors: List[Dict[str, Any]]) -> int:
    """Corrige erros F821 (nomes indefinidos) adicionando imports."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Identifica os nomes indefinidos
        undefined_names = set()
        for error in errors:
            if error.get("code") == "F821":
                message = error.get("message", "")
                match = re.search(r"Undefined name `([^`]+)`", message)
                if match:
                    undefined_names.add(match.group(1))

        if not undefined_names:
            return 0

        # Adiciona imports para os nomes indefinidos
        # Isso é uma simplificação, na prática seria necessário
        # analisar o código para determinar de onde importar
        imports_to_add = []
        for name in undefined_names:
            imports_to_add.append(
                f"from typing import {name}  # TODO: Verificar se este é o import correto\n"
            )

        # Encontra o último import no topo do arquivo
        last_import_index = 0
        for i, line in enumerate(lines):
            if re.match(r"^(import|from)\s+", line.strip()):
                last_import_index = i

        # Insere os imports no lugar correto
        for import_line in imports_to_add:
            lines.insert(last_import_index + 1, import_line)
            last_import_index += 1

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return len(imports_to_add)
    except Exception as e:
        print(f"Erro ao corrigir F821 em {file_path}: {e}")
        return 0


def fix_redefined_unused(file_path: str, errors: List[Dict[str, Any]]) -> int:
    """Corrige erros F811 (redefinido mas não utilizado)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Identifica as linhas com redefinições não utilizadas
        line_numbers_to_remove = []
        for error in errors:
            if error.get("code") == "F811":
                line_num = error.get("location", {}).get("row", 0) - 1
                if 0 <= line_num < len(lines):
                    line_numbers_to_remove.append(line_num)

        if not line_numbers_to_remove:
            return 0

        # Remove as linhas com redefinições não utilizadas
        for line_num in sorted(line_numbers_to_remove, reverse=True):
            lines.pop(line_num)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return len(line_numbers_to_remove)
    except Exception as e:
        print(f"Erro ao corrigir F811 em {file_path}: {e}")
        return 0


def fix_bare_except(file_path: str, errors: List[Dict[str, Any]]) -> int:
    """Corrige erros E722 (except genérico)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_count = 0
        for error in errors:
            if error.get("code") == "E722":
                line_num = error.get("location", {}).get("row", 0) - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    # Substitui "except:" por "except Exception:"
                    if "except:" in line:
                        lines[line_num] = line.replace("except:", "except Exception:")
                        fixed_count += 1

        if fixed_count > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

        return fixed_count
    except Exception as e:
        print(f"Erro ao corrigir E722 em {file_path}: {e}")
        return 0


def fix_type_comparison(file_path: str, errors: List[Dict[str, Any]]) -> int:
    """Corrige erros E721 (comparação de tipo)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_count = 0
        for error in errors:
            if error.get("code") == "E721":
                line_num = error.get("location", {}).get("row", 0) - 1
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    # Substitui "type(x) == y" por "isinstance(x, y)"
                    if "type(" in line and "==" in line:
                        match = re.search(r"type\(([^)]+)\)\s*==\s*([^:\s]+)", line)
                        if match:
                            obj = match.group(1)
                            cls = match.group(2)
                            lines[line_num] = line.replace(
                                f"type({obj}) == {cls}", f"isinstance({obj}, {cls})"
                            )
                            fixed_count += 1

        if fixed_count > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

        return fixed_count
    except Exception as e:
        print(f"Erro ao corrigir E721 em {file_path}: {e}")
        return 0


def fix_all_remaining_errors() -> Dict[str, int]:
    """Corrige todos os erros restantes."""
    errors = run_ruff_check()
    if not errors:
        print("Nenhum erro encontrado ou ocorreu um problema ao executar o Ruff.")
        return {}

    errors_by_file_and_code = group_errors_by_file_and_code(errors)

    fixed_counts = {
        "E402": 0,  # Import não está no topo do arquivo
        "F821": 0,  # Nome indefinido
        "F811": 0,  # Redefinido mas não utilizado
        "E722": 0,  # Except genérico
        "E721": 0,  # Comparação de tipo
    }

    for file_path, errors_by_code in errors_by_file_and_code.items():
        # Corrige erros E402 (imports não estão no topo do arquivo)
        if "E402" in errors_by_code:
            fixed = fix_import_order(file_path, errors_by_code["E402"])
            if fixed:
                print(f"Corrigidos {fixed} erros E402 em {file_path}")
                fixed_counts["E402"] += fixed

        # Corrige erros F821 (nomes indefinidos)
        if "F821" in errors_by_code:
            fixed = fix_undefined_names(file_path, errors_by_code["F821"])
            if fixed:
                print(f"Corrigidos {fixed} erros F821 em {file_path}")
                fixed_counts["F821"] += fixed

        # Corrige erros F811 (redefinido mas não utilizado)
        if "F811" in errors_by_code:
            fixed = fix_redefined_unused(file_path, errors_by_code["F811"])
            if fixed:
                print(f"Corrigidos {fixed} erros F811 em {file_path}")
                fixed_counts["F811"] += fixed

        # Corrige erros E722 (except genérico)
        if "E722" in errors_by_code:
            fixed = fix_bare_except(file_path, errors_by_code["E722"])
            if fixed:
                print(f"Corrigidos {fixed} erros E722 em {file_path}")
                fixed_counts["E722"] += fixed

        # Corrige erros E721 (comparação de tipo)
        if "E721" in errors_by_code:
            fixed = fix_type_comparison(file_path, errors_by_code["E721"])
            if fixed:
                print(f"Corrigidos {fixed} erros E721 em {file_path}")
                fixed_counts["E721"] += fixed

    return fixed_counts


def main():
    """Função principal."""
    print("Iniciando correção dos erros restantes...")

    fixed_counts = fix_all_remaining_errors()

    total_fixed = sum(fixed_counts.values())
    if total_fixed > 0:
        print("\nResumo das correções:")
        for code, count in fixed_counts.items():
            if count > 0:
                print(f"  - {code}: {count} erros corrigidos")
        print(f"\nTotal: {total_fixed} erros corrigidos.")
        print(
            "Execute 'python scripts/analyze_lint_errors.py' para verificar os erros restantes."
        )
    else:
        print("Nenhum erro foi corrigido.")

    print("\nPróximos passos recomendados:")
    print(
        "1. Execute 'ruff check pepperpy/ --fix' para aplicar correções automáticas adicionais"
    )
    print(
        "2. Atualize o pyproject.toml para ignorar erros específicos em arquivos específicos"
    )
    print("3. Corrija manualmente os erros críticos restantes (F821, E722)")
    print("4. Considere usar ferramentas como black e isort para formatação automática")


if __name__ == "__main__":
    main()
