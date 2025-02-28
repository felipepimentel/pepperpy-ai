#!/usr/bin/env python
"""
Script para validar a reestruturação do projeto PepperPy.
Este script verifica:
- Se os módulos estão nos locais esperados
- Se as dependências circulares foram eliminadas
- Se os imports estão atualizados corretamente
- Se os stubs de compatibilidade estão funcionando
"""

import os
import re
import sys
from pathlib import Path
from typing import List

# Adicionar o diretório pai ao caminho para importar o restructure.py
sys.path.append(str(Path(__file__).parent))
from restructure import PEPPERPY_DIR


def check_module_locations() -> List[str]:
    """
    Verifica se os módulos estão nos locais esperados após a reestruturação.

    Returns:
        List[str]: Lista de problemas encontrados
    """
    problems = []

    # Lista de módulos que devem existir após a reestruturação
    expected_modules = [
        "providers",  # Novo módulo centralizado de provedores
        "capabilities",  # Novo módulo de capacidades
        "workflows",  # Workflows movidos para o nível superior
        "core/errors",  # Erros consolidados no core
    ]

    # Lista de módulos que não devem mais existir como estruturas separadas
    deprecated_modules = [
        "common/errors",  # Deve ter sido consolidado em core/errors
        "agents/workflows",  # Deve ter sido movido para workflows no nível superior
        "agents/providers",  # Deve ter sido movido para providers/agent
        "audio/providers",  # Deve ter sido movido para providers/audio
    ]

    # Verifica os módulos esperados
    for module in expected_modules:
        module_path = PEPPERPY_DIR / module
        if not module_path.exists():
            problems.append(f"Módulo esperado não encontrado: {module}")

    # Verifica os módulos deprecados (devem existir apenas como stubs)
    for module in deprecated_modules:
        module_path = PEPPERPY_DIR / module
        if not module_path.exists():
            problems.append(
                f"Módulo deprecado completamente removido (deve existir como stub): {module}"
            )
        else:
            # Verifica se é apenas um stub (deve ter apenas um __init__.py)
            module_files = list(module_path.glob("*"))
            if len(module_files) > 1 or not (module_path / "__init__.py").exists():
                problems.append(
                    f"Módulo deprecado contém mais do que um stub: {module}"
                )

    return problems


def detect_circular_dependencies() -> List[str]:
    """
    Detecta dependências circulares no código.

    Returns:
        List[str]: Lista de dependências circulares encontradas
    """
    circular_deps = []
    import_graph = {}  # Módulo -> conjunto de módulos importados

    # Constrói o grafo de importações
    for root, _, files in os.walk(PEPPERPY_DIR):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                module_path = os.path.relpath(file_path, PEPPERPY_DIR)
                module_name = module_path.replace("/", ".").replace(".py", "")

                if module_name.endswith("__init__"):
                    module_name = module_name[:-9]

                import_graph[module_name] = set()

                # Extrai imports
                with open(file_path, "r") as f:
                    content = f.read()

                # Busca padrões de import
                import_patterns = [
                    r"import\s+(pepperpy\.[^\s;]+)",
                    r"from\s+(pepperpy\.[^\s;]+)\s+import",
                ]

                for pattern in import_patterns:
                    for match in re.finditer(pattern, content):
                        imported_module = match.group(1)
                        import_graph[module_name].add(imported_module)

    # Detecta ciclos usando DFS
    def has_cycle(node, visited, rec_stack):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in import_graph.get(node, []):
            if neighbor.startswith("pepperpy."):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    circular_deps.append(f"Dependência circular: {node} -> {neighbor}")
                    return True

        rec_stack.remove(node)
        return False

    # Verifica ciclos para cada nó
    visited = set()
    for node in import_graph:
        if node not in visited:
            has_cycle(node, visited, set())

    return circular_deps


def check_import_consistency() -> List[str]:
    """
    Verifica se os imports foram atualizados corretamente.

    Returns:
        List[str]: Lista de problemas de importação encontrados
    """
    problems = []

    # Mapeamento de imports antigos que não devem mais ser usados
    deprecated_imports = {
        "pepperpy.common.errors": "pepperpy.core.errors",
        "pepperpy.agents.workflows": "pepperpy.workflows",
        "pepperpy.agents.providers": "pepperpy.providers.agent",
        "pepperpy.audio.providers": "pepperpy.providers.audio",
        "pepperpy.vision.providers": "pepperpy.providers.vision",
        "pepperpy.audio": "pepperpy.capabilities.audio",
        "pepperpy.vision": "pepperpy.capabilities.vision",
        "pepperpy.cli.plugins": "pepperpy.core.plugins.cli",
    }

    # Verifica todos os arquivos Python
    for root, _, files in os.walk(PEPPERPY_DIR):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                rel_path = os.path.relpath(file_path, PEPPERPY_DIR)

                # Não verificamos os stubs de compatibilidade
                if "__init__.py" in rel_path and "from" in rel_path:
                    continue

                with open(file_path, "r") as f:
                    content = f.read()

                # Verifica cada import obsoleto
                for old_import, new_import in deprecated_imports.items():
                    # Evita falsos positivos em comentários
                    pattern = rf"[^\'\"]import\s+{re.escape(old_import)}[^\'\"]|[^\'\"]from\s+{re.escape(old_import)}\s+import[^\'\"]"
                    if re.search(pattern, content):
                        problems.append(
                            f"Import obsoleto em {rel_path}: {old_import} (deve ser {new_import})"
                        )

    return problems


def check_stub_functionality() -> List[str]:
    """
    Verifica se os stubs de compatibilidade estão funcionando corretamente.

    Returns:
        List[str]: Lista de problemas encontrados com stubs
    """
    problems = []

    # Lista de locais onde esperamos stubs de compatibilidade
    expected_stubs = [
        ("common/errors/__init__.py", "core/errors"),
        ("agents/workflows/__init__.py", "workflows"),
        ("agents/providers/__init__.py", "providers/agent"),
        ("audio/providers/__init__.py", "providers/audio"),
        ("vision/providers/__init__.py", "providers/vision"),
        ("audio/__init__.py", "capabilities/audio"),
        ("vision/__init__.py", "capabilities/vision"),
        ("cli/plugins/__init__.py", "core/plugins/cli"),
    ]

    for stub_path, target in expected_stubs:
        stub_file = PEPPERPY_DIR / stub_path
        if not stub_file.exists():
            problems.append(f"Stub de compatibilidade ausente: {stub_path}")
            continue

        with open(stub_file, "r") as f:
            content = f.read()

        # Verifica se o stub importa corretamente do novo local
        expected_import = f"from pepperpy.{target}"
        if expected_import not in content and "import *" not in content:
            problems.append(
                f"Stub de compatibilidade em {stub_path} não importa corretamente de {target}"
            )

    return problems


def main():
    """Executa todas as verificações de validação."""
    print("Validando a reestruturação do PepperPy...")

    # Lista para armazenar todos os problemas encontrados
    all_problems = []

    # Executa as verificações
    module_problems = check_module_locations()
    circular_deps = detect_circular_dependencies()
    import_problems = check_import_consistency()
    stub_problems = check_stub_functionality()

    # Combina todos os problemas
    all_problems.extend(module_problems)
    all_problems.extend(circular_deps)
    all_problems.extend(import_problems)
    all_problems.extend(stub_problems)

    # Exibe os resultados
    if all_problems:
        print(f"\n❌ {len(all_problems)} problemas encontrados após a reestruturação:")
        for i, problem in enumerate(all_problems, 1):
            print(f"{i}. {problem}")
        print("\nA reestruturação pode precisar de ajustes adicionais.")
    else:
        print(
            "\n✅ Nenhum problema encontrado! A reestruturação parece ter sido bem-sucedida."
        )

    # Retorna código de saída apropriado
    return 1 if all_problems else 0


if __name__ == "__main__":
    sys.exit(main())
