"""
Módulo para implementar a otimização de dependências no projeto PepperPy.

Este módulo:
1. Analisa dependências entre módulos
2. Identifica e remove dependências desnecessárias
3. Implementa um sistema de dependências opcionais mais claro
4. Atualiza o arquivo pyproject.toml
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Set


def find_imported_modules(file_path: Path) -> Set[str]:
    """
    Encontra módulos importados em um arquivo.

    Args:
        file_path: Caminho para o arquivo

    Returns:
        Conjunto de módulos importados
    """
    imports = set()

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Padrão para "import pepperpy.x.y"
        pattern1 = r"import\s+(pepperpy\.\w+(?:\.\w+)*)"
        for match in re.finditer(pattern1, content):
            imports.add(match.group(1))

        # Padrão para "from pepperpy.x.y import z"
        pattern2 = r"from\s+(pepperpy\.\w+(?:\.\w+)*)\s+import"
        for match in re.finditer(pattern2, content):
            imports.add(match.group(1))

    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")

    return imports


def build_dependency_graph(project_root: Path) -> Dict[str, Set[str]]:
    """
    Constrói um grafo de dependências entre módulos.

    Args:
        project_root: Diretório raiz do projeto

    Returns:
        Dicionário mapeando módulos para seus dependentes
    """
    graph = {}

    # Diretórios a ignorar
    ignore_dirs = {".git", ".venv", "__pycache__", "backup", "scripts"}

    # Analisar cada arquivo Python
    for root, dirs, files in os.walk(project_root / "pepperpy"):
        # Remover diretórios ignorados
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file

                # Obter o nome do módulo
                rel_path = file_path.relative_to(project_root)
                if file == "__init__.py":
                    module_name = str(rel_path.parent).replace("/", ".")
                else:
                    module_name = str(rel_path).replace("/", ".").replace(".py", "")

                # Encontrar módulos importados
                imports = find_imported_modules(file_path)

                # Adicionar ao grafo
                if module_name not in graph:
                    graph[module_name] = set()

                for imported in imports:
                    if imported.startswith("pepperpy."):
                        graph[module_name].add(imported)

    return graph


def identify_optional_dependencies(graph: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    """
    Identifica dependências opcionais para cada módulo do projeto.

    Args:
        graph: Grafo de dependências

    Returns:
        Dicionário de módulos com suas dependências opcionais
    """
    # Mapear módulos de alto nível
    top_level_modules = {}
    for module in graph.keys():
        parts = module.split(".")
        if len(parts) > 1:
            top_level = parts[1]
            if top_level not in top_level_modules:
                top_level_modules[top_level] = []
            top_level_modules[top_level].append(module)

    # Identificar dependências opcionais
    optional_deps = {}
    for module, imports in graph.items():
        parts = module.split(".")
        if len(parts) <= 1:
            continue

        module_group = parts[1]
        opt_deps = []

        for imported in imports:
            imported_parts = imported.split(".")
            if len(imported_parts) <= 1:
                continue

            imported_group = imported_parts[1]

            # Se o módulo importado é de um grupo diferente, é potencialmente opcional
            if imported_group != module_group:
                # Verificar se o módulo é provavelmente opcional
                if (
                    imported_group in ["providers", "capabilities", "plugins"]
                    or imported.endswith(".providers")
                    or imported.endswith(".capabilities")
                    or imported.endswith(".plugins")
                ):
                    opt_deps.append(imported)

        if opt_deps:
            optional_deps[module] = opt_deps

    return optional_deps


def update_pyproject_toml(
    project_root: Path, optional_deps: Dict[str, List[str]], backup_dir: Path
) -> bool:
    """
    Atualiza o arquivo pyproject.toml com dependências opcionais.

    Args:
        project_root: Diretório raiz do projeto
        optional_deps: Dicionário de dependências opcionais
        backup_dir: Diretório para backup

    Returns:
        True se o arquivo foi atualizado, False caso contrário
    """
    pyproject_file = project_root / "pyproject.toml"
    if not pyproject_file.exists():
        print(f"Arquivo {pyproject_file} não encontrado")
        return False

    # Criar backup
    backup_path = backup_dir / "pyproject.toml"
    shutil.copy2(pyproject_file, backup_path)

    # Ler o arquivo
    with open(pyproject_file, "r") as f:
        content = f.read()

    # Verificar se já existe uma seção [tool.poetry.extras]
    extras_section = re.search(r"\[tool\.poetry\.extras\].*?\[", content, re.DOTALL)
    if extras_section:
        extras_content = extras_section.group(0)
        # Remover o último caractere '[' capturado
        extras_content = extras_content[:-1].strip()
    else:
        # Procurar a posição para inserir a seção de extras
        deps_section = re.search(
            r"\[tool\.poetry\.dependencies\].*?\[", content, re.DOTALL
        )
        if deps_section:
            insert_pos = deps_section.end() - 1
            extras_content = "\n\n[tool.poetry.extras]\n"
            # Criar nova seção de extras
            content = content[:insert_pos] + extras_content + content[insert_pos:]
        else:
            print("Seção [tool.poetry.dependencies] não encontrada")
            return False

    # Agrupar dependências opcionais por categoria
    grouped_deps = {}
    for module, deps in optional_deps.items():
        module_parts = module.split(".")
        if len(module_parts) > 1:
            category = module_parts[1]
            if category not in grouped_deps:
                grouped_deps[category] = set()
            for dep in deps:
                dep_parts = dep.split(".")
                if len(dep_parts) > 1:
                    grouped_deps[category].add(dep_parts[1])

    # Construir a seção de extras
    extras_content = "\n\n[tool.poetry.extras]\n"
    for category, deps in grouped_deps.items():
        # Mapear para dependências externas comuns associadas a cada categoria
        external_deps = []
        if category == "providers":
            external_deps = ['"openai"', '"anthropic"', '"cohere"']
        elif category == "capabilities":
            external_deps = ['"opencv-python"', '"transformers"', '"pytorch"']
        elif category == "cloud":
            external_deps = [
                '"boto3"',
                '"google-cloud-storage"',
                '"azure-storage-blob"',
            ]

        if external_deps:
            extras_content += f"{category} = [{', '.join(external_deps)}]\n"

    # Encontrar onde inserir a seção de extras
    extra_section_match = re.search(r"\[tool\.poetry\.extras\]", content)
    if extra_section_match:
        # Encontrar o início da próxima seção
        next_section = re.search(r"\n\[tool\.", content[extra_section_match.end() :])
        if next_section:
            insert_end = extra_section_match.end() + next_section.start()
        else:
            insert_end = len(content)

        # Substituir a seção existente
        content = (
            content[: extra_section_match.start()]
            + extras_content
            + content[insert_end:]
        )
    else:
        # Adicionar ao final do arquivo
        content += extras_content

    # Escrever o arquivo atualizado
    with open(pyproject_file, "w") as f:
        f.write(content)

    return True


def generate_dependency_docs(
    project_root: Path, graph: Dict[str, Set[str]], optional_deps: Dict[str, List[str]]
) -> None:
    """
    Gera documentação sobre dependências do projeto.

    Args:
        project_root: Diretório raiz do projeto
        graph: Grafo de dependências
        optional_deps: Dicionário de dependências opcionais
    """
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    deps_doc_file = docs_dir / "dependencies.md"

    with open(deps_doc_file, "w") as f:
        f.write("# PepperPy Dependencies\n\n")
        f.write(
            "This document describes the dependency structure of the PepperPy framework.\n\n"
        )

        # Módulos de alto nível
        f.write("## Top-Level Modules\n\n")
        top_modules = {}
        for module in graph.keys():
            parts = module.split(".")
            if len(parts) > 1:
                top_level = parts[1]
                if top_level not in top_modules:
                    top_modules[top_level] = 0
                top_modules[top_level] += 1

        f.write("| Module | File Count |\n")
        f.write("|--------|------------|\n")
        for module, count in sorted(
            top_modules.items(), key=lambda x: x[1], reverse=True
        ):
            f.write(f"| `{module}` | {count} |\n")

        # Dependências opcionais
        f.write("\n## Optional Dependencies\n\n")
        f.write(
            "These dependencies are not required for core functionality, but enable additional features.\n\n"
        )

        opt_groups = {}
        for module, deps in optional_deps.items():
            module_parts = module.split(".")
            if len(module_parts) > 1:
                category = module_parts[1]
                if category not in opt_groups:
                    opt_groups[category] = {}

                for dep in deps:
                    dep_parts = dep.split(".")
                    if len(dep_parts) > 1:
                        dep_category = dep_parts[1]
                        if dep_category not in opt_groups[category]:
                            opt_groups[category][dep_category] = 0
                        opt_groups[category][dep_category] += 1

        for category, deps in sorted(opt_groups.items()):
            f.write(f"### `{category}` Optional Dependencies\n\n")
            f.write("| Dependency | Usage Count |\n")
            f.write("|------------|-------------|\n")
            for dep, count in sorted(deps.items(), key=lambda x: x[1], reverse=True):
                f.write(f"| `{dep}` | {count} |\n")
            f.write("\n")

        # Dependências externas
        f.write("\n## External Dependencies\n\n")
        f.write(
            "The PepperPy framework depends on the following external packages:\n\n"
        )
        f.write("| Package | Used By | Required |\n")
        f.write("|---------|---------|----------|\n")
        f.write("| `openai` | providers.llm | No |\n")
        f.write("| `anthropic` | providers.llm | No |\n")
        f.write("| `transformers` | capabilities.vision | No |\n")
        f.write("| `torch` | capabilities.vision | No |\n")
        f.write("| `numpy` | various modules | Yes |\n")
        f.write("| `pydantic` | various modules | Yes |\n")


def implement_lazy_imports(
    project_root: Path, optional_deps: Dict[str, List[str]], backup_dir: Path
) -> int:
    """
    Implementa importações lazy para dependências opcionais.

    Args:
        project_root: Diretório raiz do projeto
        optional_deps: Dicionário de dependências opcionais
        backup_dir: Diretório para backup

    Returns:
        Número de arquivos modificados
    """
    modified_files = 0
    lazy_import_wrapper = '''
def _lazy_import(module_name):
    """Lazy import function that loads a module only when it's used."""
    class LazyModule:
        def __init__(self, module_name):
            self.module_name = module_name
            self._module = None
            
        def __getattr__(self, name):
            if self._module is None:
                try:
                    self._module = __import__(self.module_name, fromlist=["*"])
                except ImportError as e:
                    raise ImportError(f"Optional dependency {self.module_name} is required for this feature. {e}")
            return getattr(self._module, name)
    
    return LazyModule(module_name)
'''

    # Obter módulos para cada arquivo
    file_to_module = {}
    module_to_file = {}

    for root, _, files in os.walk(project_root / "pepperpy"):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(project_root)

                if file == "__init__.py":
                    module_name = str(rel_path.parent).replace("/", ".")
                else:
                    module_name = str(rel_path).replace("/", ".").replace(".py", "")

                file_to_module[str(file_path)] = module_name
                module_to_file[module_name] = str(file_path)

    # Modificar arquivos com dependências opcionais
    for module, opt_deps in optional_deps.items():
        if module not in module_to_file:
            continue

        file_path = Path(module_to_file[module])
        if not file_path.exists():
            continue

        # Ler o conteúdo do arquivo
        with open(file_path, "r") as f:
            content = f.read()

        # Criar backup
        rel_path = file_path.relative_to(project_root)
        backup_path = backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)

        # Verificar se o arquivo já tem a função de lazy import
        has_lazy_import = "_lazy_import" in content

        # Modificar importações
        modified = False
        lines = content.split("\n")
        new_lines = []

        # Adicionar a função de lazy import se necessário
        if not has_lazy_import and opt_deps:
            # Encontrar onde adicionar a função (após imports e docstrings)
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    import_end = i
                elif (
                    line.strip()
                    and not line.startswith("#")
                    and not line.startswith('"""')
                    and not line.startswith("'''")
                ):
                    break

            # Inserir a função de lazy import
            new_lines = lines[: import_end + 1]
            new_lines.append(lazy_import_wrapper)
            new_lines.extend(lines[import_end + 1 :])
            lines = new_lines
            modified = True

        # Processar cada linha
        new_lines = []
        for line in lines:
            # Se a linha é um import de uma dependência opcional
            original_line = line
            for dep in opt_deps:
                # Substituir imports diretos
                if re.match(rf"import\s+{re.escape(dep)}", line):
                    line = f"# Optional dependency: {line}"
                    new_lines.append(line)
                    # Adicionar versão lazy
                    module_var = dep.split(".")[-1]
                    line = f"{module_var} = _lazy_import('{dep}')"
                    modified = True
                # Substituir imports from
                elif re.match(rf"from\s+{re.escape(dep)}\s+import", line):
                    # Guardar o que está sendo importado
                    match = re.match(rf"from\s+{re.escape(dep)}\s+import\s+(.+)", line)
                    if match:
                        imported_items = match.group(1)
                        line = f"# Optional dependency: {line}"
                        new_lines.append(line)
                        # Adicionar versão lazy para cada item importado
                        items = [item.strip() for item in imported_items.split(",")]
                        items_str = ", ".join(items)
                        module_var = dep.split(".")[-1]
                        line = f"{module_var} = _lazy_import('{dep}')"
                        new_lines.append(line)
                        line = f"# Access imported items via: {module_var}.{items[0]}"
                        modified = True

            if line == original_line:
                new_lines.append(line)

        # Se o arquivo foi modificado, salvar as alterações
        if modified:
            with open(file_path, "w") as f:
                f.write("\n".join(new_lines))
            modified_files += 1

    return modified_files


def implement_dependency_optimization(project_root: Path, backup_dir: Path) -> None:
    """
    Implementa otimização de dependências no projeto.

    Args:
        project_root: Diretório raiz do projeto
        backup_dir: Diretório para backup
    """
    print("Implementando otimização de dependências...")

    # 1. Construir grafo de dependências
    print("Construindo grafo de dependências...")
    graph = build_dependency_graph(project_root)
    print(f"Encontrados {len(graph)} módulos no projeto")

    # 2. Identificar dependências opcionais
    print("Identificando dependências opcionais...")
    optional_deps = identify_optional_dependencies(graph)
    print(f"Identificados {len(optional_deps)} módulos com dependências opcionais")

    # 3. Atualizar pyproject.toml
    print("Atualizando pyproject.toml com dependências opcionais...")
    if update_pyproject_toml(project_root, optional_deps, backup_dir):
        print("Arquivo pyproject.toml atualizado com sucesso")
    else:
        print("Falha ao atualizar pyproject.toml")

    # 4. Implementar lazy imports
    print("Implementando lazy imports para dependências opcionais...")
    modified_files = implement_lazy_imports(project_root, optional_deps, backup_dir)
    print(f"Modificados {modified_files} arquivos com lazy imports")

    # 5. Gerar documentação de dependências
    print("Gerando documentação de dependências...")
    generate_dependency_docs(project_root, graph, optional_deps)
    print("Documentação de dependências gerada em docs/dependencies.md")

    print("Otimização de dependências concluída!")
