"""
Módulo para implementar interfaces públicas bem definidas para o projeto PepperPy.

Este módulo:
1. Cria um diretório `interfaces` para definir APIs públicas
2. Separa a interface pública da implementação interna
3. Desenvolve uma documentação clara de quais módulos fazem parte da API pública
4. Implementa mecanismos para compatibilidade retroativa da API
"""

import os
import re
from pathlib import Path
from typing import Dict, List


class InterfaceDefinition:
    """Definição de uma interface pública."""

    def __init__(self, name: str, module_path: str, description: str):
        self.name = name
        self.module_path = module_path
        self.description = description
        self.methods: List[Dict[str, str]] = []
        self.classes: List[Dict[str, object]] = []
        self.imports: List[str] = []

    def add_method(self, name: str, signature: str, docstring: str):
        """Adiciona um método à interface."""
        self.methods.append({
            "name": name,
            "signature": signature,
            "docstring": docstring,
        })

    def add_class(self, name: str, docstring: str, methods: List[Dict[str, object]]):
        """Adiciona uma classe à interface."""
        self.classes.append({"name": name, "docstring": docstring, "methods": methods})

    def add_import(self, import_statement: str):
        """Adiciona uma importação à interface."""
        self.imports.append(import_statement)


def find_public_classes_and_functions(file_path: Path) -> Dict:
    """
    Identifica classes e funções que podem fazer parte da API pública.

    Args:
        file_path: Caminho para o arquivo Python

    Returns:
        Dicionário com métodos e classes identificados
    """
    result = {"functions": [], "classes": []}

    # Verificar se o arquivo existe
    if not file_path.exists():
        return result

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Encontrar funções definidas no módulo (não prefixadas com _)
        function_pattern = (
            r"def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\((.*?)\).*?:(.*?)(?=\n\S|\Z)"
        )
        for match in re.finditer(function_pattern, content, re.DOTALL):
            func_name = match.group(1)
            # Ignorar funções internas ou privadas
            if not func_name.startswith("_"):
                signature = match.group(2)
                body = match.group(3)

                # Extrair docstring se existir
                docstring = ""
                docstring_match = re.search(r'"""(.*?)"""', body, re.DOTALL)
                if docstring_match:
                    docstring = docstring_match.group(1).strip()

                result["functions"].append({
                    "name": func_name,
                    "signature": signature,
                    "docstring": docstring,
                })

        # Encontrar classes definidas no módulo (não prefixadas com _)
        class_pattern = r"class\s+([a-zA-Z][a-zA-Z0-9_]*)\s*(?:\((.*?)\))?\s*:(.*?)(?=\n(?:class|def|\Z))"
        for match in re.finditer(class_pattern, content, re.DOTALL):
            class_name = match.group(1)
            # Ignorar classes internas ou privadas
            if not class_name.startswith("_"):
                inheritance = match.group(2) or ""
                body = match.group(3)

                # Extrair docstring se existir
                class_docstring = ""
                docstring_match = re.search(r'"""(.*?)"""', body, re.DOTALL)
                if docstring_match:
                    class_docstring = docstring_match.group(1).strip()

                # Encontrar métodos da classe (não prefixados com _)
                methods = []
                method_pattern = r"def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\((self(?:,\s*.*?)?)\).*?:(.*?)(?=\n\s+def|\n\S|\Z)"
                for method_match in re.finditer(method_pattern, body, re.DOTALL):
                    method_name = method_match.group(1)
                    # Ignorar métodos internos ou privados
                    if not method_name.startswith("_") or method_name in [
                        "__init__",
                        "__call__",
                    ]:
                        method_signature = method_match.group(2)
                        method_body = method_match.group(3)

                        # Extrair docstring se existir
                        method_docstring = ""
                        method_docstring_match = re.search(
                            r'"""(.*?)"""', method_body, re.DOTALL
                        )
                        if method_docstring_match:
                            method_docstring = method_docstring_match.group(1).strip()

                        methods.append({
                            "name": method_name,
                            "signature": method_signature,
                            "docstring": method_docstring,
                        })

                result["classes"].append({
                    "name": class_name,
                    "inheritance": inheritance,
                    "docstring": class_docstring,
                    "methods": methods,
                })

    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")

    return result


def determine_public_modules(project_root: Path) -> List[str]:
    """
    Determina quais módulos devem ter interfaces públicas.

    Args:
        project_root: Diretório raiz do projeto

    Returns:
        Lista de caminhos relativos para módulos com interfaces públicas
    """
    public_modules = []

    # Padrões para módulos importantes
    patterns = [
        # Capabilities
        "pepperpy/capabilities/*.py",
        "pepperpy/capabilities/*/__init__.py",
        # Providers base
        "pepperpy/providers/__init__.py",
        "pepperpy/providers/base.py",
        # Workflows
        "pepperpy/workflows/*.py",
        # Core
        "pepperpy/core/*.py",
        # Outros módulos de alto nível
        "pepperpy/*.py",
    ]

    for pattern in patterns:
        pattern_path = project_root / Path(pattern)
        parent = pattern_path.parent

        if "*" in pattern:
            # Processar globbing
            name_pattern = pattern_path.name
            if name_pattern == "*.py":
                for py_file in parent.glob("*.py"):
                    if (
                        not py_file.name.startswith("_")
                        or py_file.name == "__init__.py"
                    ):
                        rel_path = py_file.relative_to(project_root)
                        public_modules.append(str(rel_path))
            elif name_pattern == "*/__init__.py":
                for init_file in parent.glob("*/"):
                    init_path = init_file / "__init__.py"
                    if init_path.exists():
                        rel_path = init_path.relative_to(project_root)
                        public_modules.append(str(rel_path))
        else:
            # Processar caminho específico
            if pattern_path.exists():
                rel_path = pattern_path.relative_to(project_root)
                public_modules.append(str(rel_path))

    return public_modules


def create_interface_file(
    module_path: str, public_elements: Dict, project_root: Path, interfaces_dir: Path
) -> InterfaceDefinition:
    """
    Cria um arquivo de interface para um módulo.

    Args:
        module_path: Caminho relativo para o módulo
        public_elements: Dicionário com elementos públicos do módulo
        project_root: Diretório raiz do projeto
        interfaces_dir: Diretório onde serão criadas as interfaces

    Returns:
        Definição da interface criada
    """
    module_parts = module_path.replace(".py", "").split("/")
    if module_parts[-1] == "__init__":
        module_parts.pop()

    # Nome do módulo importado
    import_name = ".".join(module_parts)

    # Criar nome da interface
    if len(module_parts) <= 1:
        interface_name = f"{module_parts[0].capitalize()}Interface"
    else:
        interface_name = f"{module_parts[-1].capitalize()}Interface"

    # Criar caminho da interface
    if len(module_parts) <= 2:
        interface_path = interfaces_dir / f"{module_parts[-1]}.py"
    else:
        # Criar estrutura de diretórios
        interface_subdir = interfaces_dir / "/".join(module_parts[1:-1])
        interface_subdir.mkdir(parents=True, exist_ok=True)
        interface_path = interface_subdir / f"{module_parts[-1]}.py"

    # Ler docstring do módulo original se possível
    module_docstring = ""
    module_file = project_root / module_path
    if module_file.exists():
        try:
            with open(module_file, "r") as f:
                content = f.read()
                docstring_match = re.search(r'^"""(.*?)"""', content, re.DOTALL)
                if docstring_match:
                    module_docstring = docstring_match.group(1).strip()
        except Exception as e:
            print(f"Erro ao ler docstring do módulo {module_path}: {e}")

    if not module_docstring:
        module_docstring = f"Interface pública para o módulo {import_name}."

    # Criar definição da interface
    interface = InterfaceDefinition(
        name=interface_name,
        module_path=str(interface_path),
        description=module_docstring,
    )

    # Adicionar importação do módulo original
    interface.add_import(f"from {import_name} import *")

    # Adicionar ABC para interfaces
    interface.add_import("from abc import ABC, abstractmethod")
    interface.add_import("from typing import Any, Dict, List, Optional, Union")

    # Criar diretório pai se necessário
    interface_path.parent.mkdir(parents=True, exist_ok=True)

    # Escrever o arquivo de interface
    with open(interface_path, "w") as f:
        f.write(f'"""\n{interface.description}\n"""\n\n')

        # Importações
        for imp in interface.imports:
            f.write(f"{imp}\n")
        f.write("\n\n")

        # Classes
        for cls in public_elements["classes"]:
            f.write(f"class {cls['name']}:\n")
            if cls["docstring"]:
                f.write(f'    """{cls["docstring"]}\n    """\n\n')

            # Métodos
            for method in cls["methods"]:
                f.write(f"    def {method['name']}({method['signature']}):\n")
                if method["docstring"]:
                    f.write(f'        """{method["docstring"]}\n        """\n')
                f.write("        pass\n\n")

            # Espaço entre classes
            f.write("\n")

        # Funções
        for func in public_elements["functions"]:
            f.write(f"def {func['name']}({func['signature']}):\n")
            if func["docstring"]:
                f.write(f'    """{func["docstring"]}\n    """\n')
            f.write("    pass\n\n")

    return interface


def create_interfaces_package(project_root: Path, backup_dir: Path) -> Path:
    """
    Cria o pacote de interfaces.

    Args:
        project_root: Diretório raiz do projeto
        backup_dir: Diretório para backup

    Returns:
        Caminho para o diretório de interfaces
    """
    interfaces_dir = project_root / "pepperpy" / "interfaces"

    # Criar diretório se não existir
    interfaces_dir.mkdir(exist_ok=True)

    # Criar __init__.py
    init_file = interfaces_dir / "__init__.py"
    with open(init_file, "w") as f:
        f.write('"""\n')
        f.write("Interfaces públicas do PepperPy.\n")
        f.write("\n")
        f.write("Este pacote define as interfaces públicas do framework PepperPy.\n")
        f.write(
            "Utilize estas interfaces para interagir com o framework de forma segura,\n"
        )
        f.write("garantindo compatibilidade com versões futuras.\n")
        f.write('"""\n\n')

        # Importações específicas serão adicionadas posteriormente

    return interfaces_dir


def create_public_interfaces(project_root: Path, backup_dir: Path) -> None:
    """
    Cria interfaces públicas para o projeto.

    Args:
        project_root: Diretório raiz do projeto
        backup_dir: Diretório para backup
    """
    print("Criando interfaces públicas...")

    # 1. Criar diretório de interfaces
    interfaces_dir = create_interfaces_package(project_root, backup_dir)
    print(f"Criado diretório de interfaces em {interfaces_dir}")

    # 2. Determinar módulos públicos
    public_modules = determine_public_modules(project_root)
    print(f"Identificados {len(public_modules)} módulos para interfaces públicas")

    # 3. Processar cada módulo
    interfaces = []
    for module_path in public_modules:
        try:
            file_path = project_root / module_path
            public_elements = find_public_classes_and_functions(file_path)

            # Criar interface se houver elementos públicos
            if public_elements["classes"] or public_elements["functions"]:
                interface = create_interface_file(
                    module_path, public_elements, project_root, interfaces_dir
                )
                interfaces.append(interface)
                print(f"Criada interface para {module_path}")
        except Exception as e:
            print(f"Erro ao processar {module_path}: {e}")

    # 4. Atualizar __init__.py com importações
    update_interfaces_init(interfaces_dir, interfaces)
    print("Atualizado __init__.py com importações das interfaces")

    # 5. Gerar documentação da API pública
    generate_public_api_doc(project_root, interfaces)
    print("Documentação da API pública gerada em docs/public_api.md")

    print("Interfaces públicas criadas com sucesso!")


def update_interfaces_init(
    interfaces_dir: Path, interfaces: List[InterfaceDefinition]
) -> None:
    """
    Atualiza o arquivo __init__.py do pacote interfaces.

    Args:
        interfaces_dir: Diretório do pacote interfaces
        interfaces: Lista de interfaces criadas
    """
    init_file = interfaces_dir / "__init__.py"

    # Ler conteúdo atual
    with open(init_file, "r") as f:
        content = f.read()

    # Adicionar importações
    content += "\n# Importar interfaces públicas\n"

    for interface in interfaces:
        module_path = interface.module_path
        rel_path = os.path.relpath(module_path, str(interfaces_dir))
        import_path = rel_path.replace("/", ".").replace(".py", "")

        if import_path.startswith(".."):
            continue  # Ignorar caminhos inválidos

        if import_path == "__init__":
            continue  # Ignorar o próprio __init__

        content += f"from .{import_path} import *\n"

    # Escrever conteúdo atualizado
    with open(init_file, "w") as f:
        f.write(content)


def generate_public_api_doc(
    project_root: Path, interfaces: List[InterfaceDefinition]
) -> None:
    """
    Gera documentação da API pública.

    Args:
        project_root: Diretório raiz do projeto
        interfaces: Lista de interfaces criadas
    """
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    api_doc_file = docs_dir / "public_api.md"

    with open(api_doc_file, "w") as f:
        f.write("# PepperPy Public API\n\n")
        f.write("This document describes the public API of the PepperPy framework.\n\n")
        f.write("## Overview\n\n")
        f.write("The PepperPy framework provides the following public interfaces:\n\n")

        # Agrupar interfaces por categoria
        categories = {}
        for interface in interfaces:
            module_path = interface.module_path
            parts = Path(module_path).parts

            if len(parts) <= 1:
                category = "core"
            else:
                category = parts[0]

            if category not in categories:
                categories[category] = []

            categories[category].append(interface)

        # Listar interfaces por categoria
        for category, cat_interfaces in sorted(categories.items()):
            f.write(f"### {category.capitalize()}\n\n")

            for interface in sorted(cat_interfaces, key=lambda i: i.name):
                module_name = os.path.basename(interface.module_path).replace(".py", "")
                f.write(f"- `{module_name}`: {interface.description.split('.')[0]}.\n")

            f.write("\n")

        # Detalhar cada interface
        f.write("## Interface Details\n\n")

        for category, cat_interfaces in sorted(categories.items()):
            f.write(f"### {category.capitalize()}\n\n")

            for interface in sorted(cat_interfaces, key=lambda i: i.name):
                module_path = interface.module_path
                module_name = os.path.basename(module_path).replace(".py", "")

                f.write(f"#### {module_name}\n\n")
                f.write(f"{interface.description}\n\n")

                # Verificar se o arquivo existe
                file_path = project_root / module_path
                if not file_path.exists():
                    f.write("*Interface file not found.*\n\n")
                    continue

                # Ler o conteúdo do arquivo
                try:
                    with open(file_path, "r") as module_file:
                        module_content = module_file.read()

                    # Extrair classes
                    classes = re.finditer(
                        r"class\s+([a-zA-Z][a-zA-Z0-9_]*)\s*(?:\((.*?)\))?\s*:(.*?)(?=\n(?:class|def|\Z))",
                        module_content,
                        re.DOTALL,
                    )

                    for cls_match in classes:
                        cls_name = cls_match.group(1)
                        cls_body = cls_match.group(3)

                        # Extrair docstring
                        cls_docstring = ""
                        docstring_match = re.search(r'"""(.*?)"""', cls_body, re.DOTALL)
                        if docstring_match:
                            cls_docstring = docstring_match.group(1).strip()

                        f.write(f"##### Class: `{cls_name}`\n\n")
                        f.write(f"{cls_docstring}\n\n")

                        # Extrair métodos
                        methods = re.finditer(
                            r"def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\((self(?:,\s*.*?)?)\).*?:(.*?)(?=\n\s+def|\n\S|\Z)",
                            cls_body,
                            re.DOTALL,
                        )

                        for method_match in methods:
                            method_name = method_match.group(1)
                            method_sig = method_match.group(2)
                            method_body = method_match.group(3)

                            # Ignorar métodos privados
                            if (
                                method_name.startswith("_")
                                and method_name != "__init__"
                                and method_name != "__call__"
                            ):
                                continue

                            # Extrair docstring
                            method_docstring = ""
                            method_docstring_match = re.search(
                                r'"""(.*?)"""', method_body, re.DOTALL
                            )
                            if method_docstring_match:
                                method_docstring = method_docstring_match.group(
                                    1
                                ).strip()

                            f.write(f"###### `{method_name}({method_sig})`\n\n")
                            f.write(f"{method_docstring}\n\n")

                    # Extrair funções de alto nível
                    functions = re.finditer(
                        r"^def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\((.*?)\).*?:(.*?)(?=\n(?:def|class)|\Z)",
                        module_content,
                        re.MULTILINE | re.DOTALL,
                    )

                    has_functions = False
                    for func_match in functions:
                        func_name = func_match.group(1)

                        # Ignorar funções privadas
                        if func_name.startswith("_"):
                            continue

                        if not has_functions:
                            f.write("##### Functions\n\n")
                            has_functions = True

                        func_sig = func_match.group(2)
                        func_body = func_match.group(3)

                        # Extrair docstring
                        func_docstring = ""
                        func_docstring_match = re.search(
                            r'"""(.*?)"""', func_body, re.DOTALL
                        )
                        if func_docstring_match:
                            func_docstring = func_docstring_match.group(1).strip()

                        f.write(f"###### `{func_name}({func_sig})`\n\n")
                        f.write(f"{func_docstring}\n\n")

                except Exception as e:
                    f.write(f"*Error extracting interface details: {e}*\n\n")

        # Adicionar guia de compatibilidade
        f.write("## API Compatibility Guidelines\n\n")
        f.write(
            "To ensure compatibility with future versions of PepperPy, follow these guidelines:\n\n"
        )
        f.write(
            "1. **Use only public interfaces**: Import only from the `pepperpy.interfaces` package.\n"
        )
        f.write(
            "2. **Don't rely on implementation details**: Avoid accessing internal modules or attributes.\n"
        )
        f.write(
            "3. **Check for deprecation warnings**: Features marked as deprecated will be removed in future versions.\n"
        )
        f.write(
            "4. **Use type hints**: Type hints help catch compatibility issues early.\n"
        )
        f.write(
            "5. **Read the documentation**: The documentation provides important information about API usage and changes.\n"
        )


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    backup_dir = project_root / "backup" / "interfaces"
    create_public_interfaces(project_root, backup_dir)
