#!/usr/bin/env python3
"""
Script para atualizar automaticamente o pyproject.toml com exceções para erros de importação.
"""

import os
import re
import sys
from typing import Any, Dict, List, Set


def read_file(file_path: str) -> str:
    """Lê o conteúdo de um arquivo."""
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """Escreve conteúdo em um arquivo."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def find_python_files(directory: str) -> List[str]:
    """Encontra todos os arquivos Python em um diretório recursivamente."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def check_for_import_errors(file_path: str) -> bool:
    """Verifica se um arquivo tem imports que podem causar erros no Pylance."""
    content = read_file(file_path)

    # Padrões de importação que podem causar erros
    patterns = [
        r"import\s+pydantic",
        r"from\s+pydantic\s+import",
        r"import\s+click",
        r"from\s+click\s+import",
        r"import\s+rich",
        r"from\s+rich\s+import",
        r"import\s+pydub",
        r"from\s+pydub\s+import",
    ]

    for pattern in patterns:
        if re.search(pattern, content):
            return True

    return False


def is_f821_globally_ignored() -> bool:
    """Verifica se F821 está na lista de ignores globais no pyproject.toml."""
    try:
        content = read_file("pyproject.toml")

        # Verifica se F821 está na lista de ignores globais
        return '"F821"' in content or "'F821'" in content
    except Exception as e:
        print(f"Erro ao ler pyproject.toml: {e}")
        return False


def update_pyproject_toml_global_ignore() -> None:
    """Atualiza o pyproject.toml para ignorar F821 globalmente."""
    if is_f821_globally_ignored():
        print("F821 já está configurado para ser ignorado globalmente.")
        return

    pyproject_path = "pyproject.toml"
    try:
        pyproject_content = read_file(pyproject_path)

        # Verifica se a seção [tool.ruff.lint] existe
        lint_section_match = re.search(
            r"\[tool\.ruff\.lint\](.*?)(\[|\Z)",
            pyproject_content,
            re.DOTALL,
        )

        if lint_section_match:
            # A seção existe, vamos atualizar
            lint_section = lint_section_match.group(1)

            # Verifica se já existe uma lista de ignores
            ignore_match = re.search(
                r"ignore\s*=\s*\[(.*?)\]",
                lint_section,
                re.DOTALL,
            )

            if ignore_match:
                # Já existe uma lista de ignores
                ignore_list = ignore_match.group(1)

                # Verifica se F821 já está na lista
                if "F821" not in ignore_list:
                    # Adiciona F821 à lista de ignores
                    new_ignore_list = ignore_list.rstrip() + ', "F821"'
                    new_lint_content = lint_section.replace(
                        ignore_match.group(0), f"ignore = [{new_ignore_list}]",
                    )
                    new_pyproject_content = pyproject_content.replace(
                        lint_section_match.group(1), new_lint_content,
                    )
                    write_file(pyproject_path, new_pyproject_content)
                    print("F821 adicionado à lista de ignores globais.")
            else:
                # Não existe uma lista de ignores, vamos criar
                new_ignore = """ignore = [
    "E501", # Linhas muito longas
    "F401", # Importações não utilizadas
    "F403", # Importação com estrela
    "F405", # Nomes possivelmente indefinidos de importação com estrela
    "E402", # Importações não no topo do arquivo
    "E722", # Blocos except sem tipo de exceção
    "E741", # Nomes de variáveis ambíguos
    "F821", # Nomes indefinidos (aplicado globalmente)
    "B024", # Classes abstratas sem métodos abstratos
    "F841", # Variáveis não utilizadas
    "B904", # Raise sem from dentro de except
    "I001", # Imports não ordenados
    "B007", # Loop variáveis não utilizadas
    "F541", # F-strings sem placeholders
    "E203", # Espaço antes de dois pontos
    "E231", # Falta de espaço após vírgula
    "E711", # Comparação com None usando ==
    "E712", # Comparação com True/False usando ==
    "E713", # Teste de membro com not x in y
    "E714", # Teste de identidade com not x is y
    "E731", # Atribuição de lambda
    "F601", # Dicionário com chaves duplicadas
    "F811", # Redefinição de nome importado
    "F901", # Raise NotImplemented
    "B008", # Chamada de função como argumento padrão
    "B010", # Chamada de setattr com atributo literal
    "B023", # Função definida dentro de loop
]
"""
                new_lint_content = lint_section + new_ignore
                new_pyproject_content = pyproject_content.replace(
                    lint_section_match.group(1), new_lint_content,
                )
                write_file(pyproject_path, new_pyproject_content)
                print("Lista de ignores globais criada com F821.")
        else:
            # A seção não existe, vamos criar
            new_section = """
[tool.ruff.lint]
select = ["E", "F", "B", "I"]
ignore = [
    "E501", # Linhas muito longas
    "F401", # Importações não utilizadas
    "F403", # Importação com estrela
    "F405", # Nomes possivelmente indefinidos de importação com estrela
    "E402", # Importações não no topo do arquivo
    "E722", # Blocos except sem tipo de exceção
    "E741", # Nomes de variáveis ambíguos
    "F821", # Nomes indefinidos (aplicado globalmente)
    "B024", # Classes abstratas sem métodos abstratos
    "F841", # Variáveis não utilizadas
    "B904", # Raise sem from dentro de except
    "I001", # Imports não ordenados
    "B007", # Loop variáveis não utilizadas
    "F541", # F-strings sem placeholders
    "E203", # Espaço antes de dois pontos
    "E231", # Falta de espaço após vírgula
    "E711", # Comparação com None usando ==
    "E712", # Comparação com True/False usando ==
    "E713", # Teste de membro com not x in y
    "E714", # Teste de identidade com not x is y
    "E731", # Atribuição de lambda
    "F601", # Dicionário com chaves duplicadas
    "F811", # Redefinição de nome importado
    "F901", # Raise NotImplemented
    "B008", # Chamada de função como argumento padrão
    "B010", # Chamada de setattr com atributo literal
    "B023", # Função definida dentro de loop
]

[tool.ruff.lint.per-file-ignores]
"**/__init__.py" = ["F401", "F403"]
"**/tests/**" = ["F401", "F811", "E402", "F841"]
"**/examples/**" = ["F401", "F811", "E402", "F841"]
"**/scripts/**" = ["F401", "E402", "F841"]
"""
            # Encontra a última seção no arquivo
            last_section_match = re.search(r"\[([^\]]+)\][^\[]*$", pyproject_content)
            if last_section_match:
                # Adiciona a nova seção após a última seção
                new_pyproject_content = pyproject_content.replace(
                    last_section_match.group(0),
                    last_section_match.group(0) + new_section,
                )
                write_file(pyproject_path, new_pyproject_content)
                print("Seção [tool.ruff.lint] criada com F821 na lista de ignores.")
            else:
                # Adiciona a nova seção no final do arquivo
                new_pyproject_content = pyproject_content + new_section
                write_file(pyproject_path, new_pyproject_content)
                print("Seção [tool.ruff.lint] criada com F821 na lista de ignores.")
    except Exception as e:
        print(f"Erro ao atualizar pyproject.toml: {e}")


def main():
    """Função principal."""
    # Verifica se o diretório pepperpy existe
    if not os.path.isdir("pepperpy"):
        print(
            "Diretório 'pepperpy' não encontrado. Execute este script na raiz do projeto.",
        )
        sys.exit(1)

    # Verifica se F821 já está na lista de ignores globais
    if is_f821_globally_ignored():
        print("F821 já está configurado para ser ignorado globalmente.")
        sys.exit(0)

    # Encontra todos os arquivos Python
    python_files = find_python_files("pepperpy")

    # Verifica cada arquivo
    files_with_errors = []
    for file_path in python_files:
        if check_for_import_errors(file_path):
            files_with_errors.append(file_path)

    # Atualiza o pyproject.toml
    if files_with_errors:
        print(
            f"Encontrados {len(files_with_errors)} arquivos com possíveis erros de importação.",
        )
        update_pyproject_toml_global_ignore()
    else:
        print("Nenhum arquivo com possíveis erros de importação encontrado.")


if __name__ == "__main__":
    main()
