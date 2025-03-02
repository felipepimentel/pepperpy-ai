#!/usr/bin/env python3
"""
Script para consolidar arquivos base.py duplicados.

Este script identifica e consolida arquivos base.py duplicados em diretórios
providers e seus subdiretórios base/, fazendo com que os arquivos duplicados
importem do arquivo base.py principal.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


def find_base_files() -> Dict[str, List[str]]:
    """
    Encontra todos os arquivos base.py no projeto e os agrupa por módulo.

    Returns:
        Dict[str, List[str]]: Dicionário com módulos como chaves e listas de caminhos de arquivos base.py como valores.
    """
    base_files = {}
    root_dir = Path("pepperpy")

    print(f"Procurando arquivos base.py em {root_dir.absolute()}")

    for module_dir in [d for d in root_dir.iterdir() if d.is_dir()]:
        module_name = module_dir.name
        base_files[module_name] = []

        # Arquivo base.py principal do módulo
        main_base = module_dir / "base.py"
        if main_base.exists():
            print(f"Encontrado arquivo base principal: {main_base}")
            base_files[module_name].append(str(main_base))

        # Arquivo base.py no diretório providers
        providers_dir = module_dir / "providers"
        if providers_dir.exists():
            providers_base = providers_dir / "base.py"
            if providers_base.exists():
                print(f"Encontrado arquivo base em providers: {providers_base}")
                base_files[module_name].append(str(providers_base))

            # Arquivo base.py no subdiretório base do diretório providers
            providers_base_dir = providers_dir / "base"
            if providers_base_dir.exists():
                providers_base_base = providers_base_dir / "base.py"
                if providers_base_base.exists():
                    print(
                        f"Encontrado arquivo base em providers/base: {providers_base_base}"
                    )
                    base_files[module_name].append(str(providers_base_base))

    # Filtrar apenas módulos com múltiplos arquivos base.py
    duplicated = {k: v for k, v in base_files.items() if len(v) > 1}
    print(f"Módulos com arquivos base.py duplicados: {list(duplicated.keys())}")
    return duplicated


def analyze_base_file(file_path: str) -> Tuple[str, Set[str], List[str]]:
    """
    Analisa um arquivo base.py para extrair seu docstring, classes e imports.

    Args:
        file_path: Caminho para o arquivo base.py

    Returns:
        Tuple[str, Set[str], List[str]]: Docstring, conjunto de nomes de classes e lista de imports
    """
    print(f"Analisando arquivo: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extrair docstring
    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    docstring = docstring_match.group(0) if docstring_match else '"""Base module."""'

    # Extrair classes
    class_matches = re.findall(r"class\s+(\w+)", content)
    classes = set(class_matches)
    print(f"  Classes encontradas: {classes}")

    # Extrair imports
    import_lines = []
    for line in content.split("\n"):
        if line.startswith("import ") or line.startswith("from "):
            import_lines.append(line)

    return docstring, classes, import_lines


def generate_consolidated_file(
    main_file: str, secondary_file: str, module_name: str
) -> str:
    """
    Gera o conteúdo consolidado para um arquivo base.py secundário.

    Args:
        main_file: Caminho para o arquivo base.py principal
        secondary_file: Caminho para o arquivo base.py secundário
        module_name: Nome do módulo

    Returns:
        str: Conteúdo consolidado para o arquivo secundário
    """
    print(f"Gerando conteúdo consolidado para {secondary_file} baseado em {main_file}")
    main_docstring, main_classes, _ = analyze_base_file(main_file)
    secondary_docstring, secondary_classes, secondary_imports = analyze_base_file(
        secondary_file
    )

    if not main_classes:
        print(f"AVISO: Nenhuma classe encontrada no arquivo principal {main_file}")
        return None

    # Criar imports das classes do arquivo principal
    main_import = f"from pepperpy.{module_name}.base import (\n"
    for cls in sorted(main_classes):
        main_import += f"    {cls},\n"
    main_import += ")\n"

    # Criar conteúdo consolidado
    content = [
        secondary_docstring,
        "",
        "from typing import Any, Dict, List, Optional, Union",
        "",
        main_import,
        "",
        "# Re-export classes from the main base module",
        "__all__ = [",
    ]

    for cls in sorted(main_classes):
        content.append(f'    "{cls}",')

    content.append("]")

    return "\n".join(content)


def update_base_files(duplicated_base_files: Dict[str, List[str]]) -> None:
    """
    Atualiza os arquivos base.py duplicados para importar do arquivo principal.

    Args:
        duplicated_base_files: Dicionário com módulos como chaves e listas de caminhos de arquivos base.py como valores.
    """
    for module_name, files in duplicated_base_files.items():
        if len(files) < 2:
            continue

        main_file = files[0]  # Arquivo base.py principal do módulo
        print(f"\nProcessando módulo {module_name}:")
        print(f"  Arquivo principal: {main_file}")

        for secondary_file in files[1:]:
            print(f"  Arquivo secundário: {secondary_file}")
            consolidated_content = generate_consolidated_file(
                main_file, secondary_file, module_name
            )

            if consolidated_content:
                print(f"  Atualizando {secondary_file}...")
                with open(secondary_file, "w", encoding="utf-8") as f:
                    f.write(consolidated_content)
            else:
                print(f"  ERRO: Não foi possível gerar conteúdo para {secondary_file}")


def main():
    """Função principal do script."""
    print("Consolidando arquivos base.py duplicados...")
    duplicated_base_files = find_base_files()

    if not duplicated_base_files:
        print("Nenhum arquivo base.py duplicado encontrado.")
        return

    print(
        f"\nEncontrados {len(duplicated_base_files)} módulos com arquivos base.py duplicados:"
    )
    for module, files in duplicated_base_files.items():
        print(f"  - {module}: {len(files)} arquivos")
        for file in files:
            print(f"    - {file}")

    update_base_files(duplicated_base_files)
    print("\nConsolidação concluída com sucesso!")


if __name__ == "__main__":
    main()
