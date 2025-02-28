"""
Módulo para consolidação de utilitários no projeto PepperPy.

Este módulo:
1. Identifica utilidades espalhadas pelo projeto
2. Consolida funções e classes semelhantes em módulos compartilhados
3. Move utilitários para um módulo centralizado
4. Atualiza as importações em todo o projeto
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


def find_utility_files(project_root: Path) -> List[Path]:
    """
    Encontra arquivos que contêm funções utilitárias.

    Args:
        project_root: Diretório raiz do projeto

    Returns:
        Lista de caminhos para arquivos utilitários
    """
    utility_patterns = [
        r"utils\.py$",
        r"helpers\.py$",
        r"util/",
        r"utilities/",
        r"common/",
    ]

    utility_files = []
    pepperpy_dir = project_root / "pepperpy"

    for root, _, files in os.walk(pepperpy_dir):
        root_path = Path(root)

        # Verificar se o diretório contém utilitários
        if any(re.search(pattern, str(root_path)) for pattern in utility_patterns):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    utility_files.append(root_path / file)
        else:
            # Verificar arquivos individuais
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    if any(re.search(pattern, file) for pattern in utility_patterns):
                        utility_files.append(root_path / file)

    return utility_files


def analyze_utility_functions(
    utility_files: List[Path],
) -> Dict[str, List[Tuple[Path, str, str]]]:
    """
    Analisa funções utilitárias e identifica duplicações ou semelhantes.

    Args:
        utility_files: Lista de arquivos utilitários

    Returns:
        Dicionário agrupando funções por categoria
    """
    # Categorias de utilidades
    categories = {
        "string": [],
        "file": [],
        "date": [],
        "format": [],
        "validation": [],
        "conversion": [],
        "network": [],
        "misc": [],
    }

    # Padrões para identificar categorias
    category_patterns = {
        "string": [r"str", r"text", r"format", r"encode", r"decode"],
        "file": [r"file", r"path", r"dir", r"folder", r"read", r"write"],
        "date": [r"date", r"time", r"timestamp", r"datetime"],
        "format": [r"format", r"pretty", r"print", r"output"],
        "validation": [r"valid", r"check", r"verify", r"ensure"],
        "conversion": [r"convert", r"transform", r"to_", r"from_"],
        "network": [r"http", r"url", r"request", r"api", r"endpoint"],
    }

    # Paddrão para encontrar funções
    function_pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*(?:->.*?)?:"

    for file_path in utility_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Encontrar todas as funções no arquivo
            for match in re.finditer(function_pattern, content, re.DOTALL):
                func_name = match.group(1)
                func_params = match.group(2)

                # Pular funções privadas e métodos de classe (começando com self)
                if func_name.startswith("_") or func_params.strip().startswith("self"):
                    continue

                # Extrair docstring, se existir
                func_body_start = match.end()
                next_line = content[func_body_start:].lstrip().split("\n")[0]
                docstring = ""

                if next_line.strip().startswith('"""') or next_line.strip().startswith(
                    "'''"
                ):
                    docstring_pattern = r'"""(.*?)"""|\'\'\'(.*?)\'\'\''
                    docstring_match = re.search(
                        docstring_pattern, content[func_body_start:], re.DOTALL
                    )
                    if docstring_match:
                        docstring = docstring_match.group(1) or docstring_match.group(2)

                # Determinar categoria
                category = "misc"
                for cat, patterns in category_patterns.items():
                    if any(
                        re.search(pattern, func_name, re.IGNORECASE)
                        for pattern in patterns
                    ):
                        category = cat
                        break

                # Adicionar função à categoria
                categories[category].append((file_path, func_name, docstring))

        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}")

    return categories


def create_utils_module(project_root: Path) -> Path:
    """
    Cria o módulo centralizado de utilitários.

    Args:
        project_root: Diretório raiz do projeto

    Returns:
        Caminho para o módulo de utilitários
    """
    utils_dir = project_root / "pepperpy" / "utils"
    utils_dir.mkdir(exist_ok=True)

    # Criar __init__.py
    init_path = utils_dir / "__init__.py"
    with open(init_path, "w", encoding="utf-8") as f:
        f.write('"""Central utilities module for PepperPy."""\n\n')
        f.write("from pepperpy.utils.string import *  # noqa\n")
        f.write("from pepperpy.utils.file import *  # noqa\n")
        f.write("from pepperpy.utils.date import *  # noqa\n")
        f.write("from pepperpy.utils.format import *  # noqa\n")
        f.write("from pepperpy.utils.validation import *  # noqa\n")
        f.write("from pepperpy.utils.conversion import *  # noqa\n")
        f.write("from pepperpy.utils.network import *  # noqa\n")
        f.write("from pepperpy.utils.misc import *  # noqa\n")

    # Criar arquivos para cada categoria
    for category in [
        "string",
        "file",
        "date",
        "format",
        "validation",
        "conversion",
        "network",
        "misc",
    ]:
        category_file = utils_dir / f"{category}.py"
        with open(category_file, "w", encoding="utf-8") as f:
            f.write(f'"""{category.capitalize()} utilities for PepperPy."""\n\n')

    return utils_dir


def migrate_utilities(
    categories: Dict[str, List[Tuple[Path, str, str]]],
    utils_dir: Path,
    backup_dir: Path,
) -> Dict[str, List[str]]:
    """
    Migra as funções utilitárias para o módulo centralizado.

    Args:
        categories: Categorias de funções utilitárias
        utils_dir: Diretório do módulo de utilitários
        backup_dir: Diretório para backup

    Returns:
        Dicionário mapeando arquivos originais para funções migradas
    """
    migration_map = {}

    for category, functions in categories.items():
        if not functions:
            continue

        category_file = utils_dir / f"{category}.py"

        with open(category_file, "a", encoding="utf-8") as f:
            for file_path, func_name, docstring in functions:
                # Verificar se o arquivo já existe no mapa
                if str(file_path) not in migration_map:
                    migration_map[str(file_path)] = []

                # Adicionar função à lista de funções migradas
                migration_map[str(file_path)].append(func_name)

                # Extrair o código da função
                with open(file_path, "r", encoding="utf-8") as source_file:
                    source_content = source_file.read()

                # Encontrar a definição completa da função
                function_pattern = rf"def\s+{re.escape(func_name)}\s*\((.*?)\)\s*(?:->.*?)?:(.*?)(?=\n\S|\Z)"
                function_match = re.search(function_pattern, source_content, re.DOTALL)

                if function_match:
                    function_params = function_match.group(1)
                    function_body = function_match.group(2)

                    # Escrever função no novo arquivo
                    f.write(f"\n\ndef {func_name}({function_params}):{function_body}\n")

                    # Backups
                    rel_path = file_path.relative_to(utils_dir.parent.parent)
                    backup_path = backup_dir / rel_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)

                    if not backup_path.exists():
                        shutil.copy2(file_path, backup_path)

    return migration_map


def update_imports_in_file(
    file_path: Path, migration_map: Dict[str, List[str]]
) -> bool:
    """
    Atualiza os imports em um arquivo.

    Args:
        file_path: Caminho do arquivo
        migration_map: Mapa de migração

    Returns:
        True se o arquivo foi modificado, False caso contrário
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Encontrar todas as importações de funções migradas
        imports_to_update = set()

        for source_file, functions in migration_map.items():
            for func_name in functions:
                # Importação direta
                import_pattern = rf"from\s+.*\s+import\s+.*{re.escape(func_name)}"
                if re.search(import_pattern, content):
                    imports_to_update.add(func_name)

        if imports_to_update:
            # Adicionar importações do novo módulo de utilitários
            new_imports = (
                "\n# Importações atualizadas para o módulo utils centralizado\n"
            )
            new_imports += (
                "from pepperpy.utils import "
                + ", ".join(sorted(imports_to_update))
                + "\n"
            )

            # Remover importações antigas
            for func_name in imports_to_update:
                content = re.sub(
                    rf"from\s+.*\s+import\s+.*{re.escape(func_name)}.*?\n", "", content
                )

            # Adicionar novas importações após a última importação existente
            import_section_end = 0
            for match in re.finditer(r"^(?:from|import)\s+.*?$", content, re.MULTILINE):
                import_section_end = max(import_section_end, match.end())

            if import_section_end > 0:
                content = (
                    content[:import_section_end]
                    + "\n"
                    + new_imports
                    + content[import_section_end:]
                )
            else:
                content = new_imports + content

        # Escrever conteúdo modificado
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Erro ao atualizar imports em {file_path}: {e}")
        return False


def update_all_imports(project_root: Path, migration_map: Dict[str, List[str]]) -> int:
    """
    Atualiza todos os imports no projeto.

    Args:
        project_root: Diretório raiz do projeto
        migration_map: Mapa de migração

    Returns:
        Número de arquivos modificados
    """
    modified_count = 0
    pepperpy_dir = project_root / "pepperpy"

    for root, _, files in os.walk(pepperpy_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file

                # Não atualizar o próprio módulo de utilitários
                if str(file_path).startswith(str(pepperpy_dir / "utils")):
                    continue

                if update_imports_in_file(file_path, migration_map):
                    modified_count += 1

    return modified_count


def generate_utils_docs(
    project_root: Path, categories: Dict[str, List[Tuple[Path, str, str]]]
) -> None:
    """
    Gera documentação para o módulo de utilitários.

    Args:
        project_root: Diretório raiz do projeto
        categories: Categorias de funções utilitárias
    """
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    utils_doc_file = docs_dir / "utils_reference.md"

    with open(utils_doc_file, "w", encoding="utf-8") as f:
        f.write("# PepperPy Utilities Reference\n\n")
        f.write(
            "This document provides a reference for all utility functions in the PepperPy framework.\n\n"
        )

        # Total de funções
        total_functions = sum(len(functions) for functions in categories.values())
        f.write("## Overview\n\n")
        f.write(
            f"PepperPy provides {total_functions} utility functions organized into {len(categories)} categories:\n\n"
        )

        for category in sorted(categories.keys()):
            function_count = len(categories[category])
            if function_count > 0:
                f.write(f"- **{category.capitalize()}**: {function_count} functions\n")

        f.write("\n## Categories\n\n")

        # Detalhes por categoria
        for category in sorted(categories.keys()):
            functions = categories[category]
            if not functions:
                continue

            f.write(f"### {category.capitalize()} Utilities\n\n")
            f.write(f"*Module: `pepperpy.utils.{category}`*\n\n")

            for _, func_name, docstring in sorted(functions, key=lambda x: x[1]):
                f.write(f"#### `{func_name}`\n\n")

                if docstring:
                    f.write(f"{docstring}\n\n")
                else:
                    f.write("*No documentation available.*\n\n")

            f.write("\n")


def implement_utils_consolidation(project_root: Path, backup_dir: Path) -> None:
    """
    Implementa a consolidação de utilitários.

    Args:
        project_root: Diretório raiz do projeto
        backup_dir: Diretório para backup
    """
    print("Implementando consolidação de utilitários...")

    # 1. Encontrar arquivos utilitários
    print("Encontrando arquivos utilitários...")
    utility_files = find_utility_files(project_root)
    print(f"Encontrados {len(utility_files)} arquivos utilitários")

    # 2. Analisar funções utilitárias
    print("Analisando funções utilitárias...")
    categories = analyze_utility_functions(utility_files)

    # Contar funções
    total_functions = sum(len(functions) for functions in categories.values())
    print(
        f"Encontradas {total_functions} funções utilitárias em {len(categories)} categorias"
    )

    # 3. Criar módulo de utilitários
    print("Criando módulo centralizado de utilitários...")
    utils_dir = create_utils_module(project_root)

    # 4. Migrar utilitários
    print("Migrando funções utilitárias...")
    migration_map = migrate_utilities(categories, utils_dir, backup_dir)

    # 5. Atualizar imports
    print("Atualizando imports...")
    modified_count = update_all_imports(project_root, migration_map)
    print(f"Atualizados imports em {modified_count} arquivos")

    # 6. Gerar documentação
    print("Gerando documentação de utilitários...")
    generate_utils_docs(project_root, categories)

    print("Consolidação de utilitários concluída!")
