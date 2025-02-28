"""
Módulo para padronização de documentação no projeto PepperPy.

Este módulo:
1. Define um padrão de documentação para classes, métodos e funções
2. Cria templates para diferentes tipos de documentação
3. Gera documentação automatizada usando docstrings
4. Verifica e corrige padrões de documentação no código existente
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set


def find_python_files(project_root: Path, exclude_dirs: Set[str] = set()) -> List[Path]:
    """
    Encontra todos os arquivos Python no projeto.

    Args:
        project_root: Diretório raiz do projeto
        exclude_dirs: Conjunto de diretórios a serem excluídos

    Returns:
        Lista de caminhos para os arquivos Python
    """
    if exclude_dirs is None:
        exclude_dirs = {".git", ".venv", "__pycache__", "backup", "scripts"}

    python_files = []

    for root, dirs, files in os.walk(project_root / "pepperpy"):
        # Remover diretórios ignorados
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                python_files.append(file_path)

    return python_files


def extract_docstring_info(file_path: Path) -> Dict:
    """
    Extrai informações sobre docstrings em um arquivo.

    Args:
        file_path: Caminho para o arquivo Python

    Returns:
        Dicionário com informações sobre as docstrings
    """
    result = {
        "has_module_docstring": False,
        "classes": [],
        "functions": [],
        "missing_docstrings": [],
        "non_standard_docstrings": [],
    }

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Verificar docstring do módulo
        module_docstring_match = re.match(r'^\s*"""(.*?)"""', content, re.DOTALL)
        result["has_module_docstring"] = bool(module_docstring_match)

        if module_docstring_match:
            module_docstring = module_docstring_match.group(1).strip()
            result["module_docstring"] = module_docstring

            # Verificar se o formato da docstring é padrão
            if not re.search(
                r"^[A-Z].*\.$", module_docstring.split("\n")[0], re.DOTALL
            ):
                result["non_standard_docstrings"].append({
                    "type": "module",
                    "name": file_path.name,
                    "line": 1,
                    "issue": "Primeira linha deve começar com letra maiúscula e terminar com ponto.",
                })
        else:
            result["missing_docstrings"].append({
                "type": "module",
                "name": file_path.name,
                "line": 1,
                "suggestion": f"Documentação do módulo {file_path.name}.",
            })

        # Encontrar classes
        class_pattern = r"class\s+([a-zA-Z][a-zA-Z0-9_]*)\s*(?:\((.*?)\))?\s*:(.*?)(?=\n(?:class|def|\Z))"
        for i, match in enumerate(re.finditer(class_pattern, content, re.DOTALL)):
            class_name = match.group(1)
            class_body = match.group(3)

            # Encontrar a linha da definição da classe
            lines = content[: match.start()].split("\n")
            line_number = len(lines)

            class_info = {
                "name": class_name,
                "line": line_number,
                "has_docstring": False,
                "methods": [],
            }

            # Verificar docstring da classe
            docstring_match = re.search(r'^\s*"""(.*?)"""', class_body, re.DOTALL)
            class_info["has_docstring"] = bool(docstring_match)

            if docstring_match:
                class_docstring = docstring_match.group(1).strip()
                class_info["docstring"] = class_docstring

                # Verificar formato da docstring
                if not re.search(
                    r"^[A-Z].*\.$", class_docstring.split("\n")[0], re.DOTALL
                ):
                    result["non_standard_docstrings"].append({
                        "type": "class",
                        "name": class_name,
                        "line": line_number,
                        "issue": "Primeira linha deve começar com letra maiúscula e terminar com ponto.",
                    })
            else:
                result["missing_docstrings"].append({
                    "type": "class",
                    "name": class_name,
                    "line": line_number,
                    "suggestion": f"Classe para {class_name}.",
                })

            # Encontrar métodos da classe
            method_pattern = r"def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\((self(?:,\s*.*?)?)\).*?:(.*?)(?=\n\s+def|\n\S|\Z)"
            for method_match in re.finditer(method_pattern, class_body, re.DOTALL):
                method_name = method_match.group(1)
                method_signature = method_match.group(2)
                method_body = method_match.group(3)

                # Encontrar a linha da definição do método
                method_start = match.start() + method_match.start()
                method_lines = content[:method_start].split("\n")
                method_line_number = len(method_lines)

                method_info = {
                    "name": method_name,
                    "line": method_line_number,
                    "has_docstring": False,
                }

                # Verificar docstring do método
                method_docstring_match = re.search(
                    r'^\s*"""(.*?)"""', method_body, re.DOTALL
                )
                method_info["has_docstring"] = bool(method_docstring_match)

                if method_docstring_match:
                    method_docstring = method_docstring_match.group(1).strip()
                    method_info["docstring"] = method_docstring

                    # Verificar formato da docstring
                    if not re.search(
                        r"^[A-Z].*\.$", method_docstring.split("\n")[0], re.DOTALL
                    ):
                        result["non_standard_docstrings"].append({
                            "type": "method",
                            "name": f"{class_name}.{method_name}",
                            "line": method_line_number,
                            "issue": "Primeira linha deve começar com letra maiúscula e terminar com ponto.",
                        })
                # Não sinalizar métodos privados ou especiais sem docstring
                elif not method_name.startswith("_"):
                    result["missing_docstrings"].append({
                        "type": "method",
                        "name": f"{class_name}.{method_name}",
                        "line": method_line_number,
                        "suggestion": f"Método {method_name} da classe {class_name}.",
                    })

                class_info["methods"].append(method_info)

            result["classes"].append(class_info)

        # Encontrar funções de alto nível
        function_pattern = (
            r"^def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\((.*?)\).*?:(.*?)(?=\n(?:def|class)|\Z)"
        )
        for match in re.finditer(function_pattern, content, re.MULTILINE | re.DOTALL):
            func_name = match.group(1)
            func_signature = match.group(2)
            func_body = match.group(3)

            # Encontrar a linha da definição da função
            lines = content[: match.start()].split("\n")
            line_number = len(lines)

            func_info = {"name": func_name, "line": line_number, "has_docstring": False}

            # Verificar docstring da função
            func_docstring_match = re.search(r'^\s*"""(.*?)"""', func_body, re.DOTALL)
            func_info["has_docstring"] = bool(func_docstring_match)

            if func_docstring_match:
                func_docstring = func_docstring_match.group(1).strip()
                func_info["docstring"] = func_docstring

                # Verificar formato da docstring
                if not re.search(
                    r"^[A-Z].*\.$", func_docstring.split("\n")[0], re.DOTALL
                ):
                    result["non_standard_docstrings"].append({
                        "type": "function",
                        "name": func_name,
                        "line": line_number,
                        "issue": "Primeira linha deve começar com letra maiúscula e terminar com ponto.",
                    })

                # Verificar se tem seções Args/Returns
                has_args_section = "Args:" in func_docstring
                has_returns_section = "Returns:" in func_docstring

                # Verificar se os parâmetros estão documentados
                if func_signature and not has_args_section:
                    result["non_standard_docstrings"].append({
                        "type": "function",
                        "name": func_name,
                        "line": line_number,
                        "issue": "Função com parâmetros deve ter seção Args:",
                    })
            # Não sinalizar funções privadas sem docstring
            elif not func_name.startswith("_"):
                result["missing_docstrings"].append({
                    "type": "function",
                    "name": func_name,
                    "line": line_number,
                    "suggestion": f"Função {func_name}.",
                })

            result["functions"].append(func_info)

    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")

    return result


def generate_standard_docstring(
    name: str,
    docstring_type: str,
    params: Optional[List[str]] = None,
    returns: Optional[str] = None,
) -> str:
    """
    Gera uma docstring padrão.

    Args:
        name: Nome do elemento (classe, método ou função)
        docstring_type: Tipo de docstring (module, class, method, function)
        params: Lista de parâmetros (opcional)
        returns: Descrição do retorno (opcional)

    Returns:
        Docstring no formato padrão
    """
    docstring = f"{name}.\n\n"

    if params:
        docstring += "Args:\n"
        for param in params:
            docstring += f"    {param}: Descrição do parâmetro.\n"
        docstring += "\n"

    if returns:
        docstring += "Returns:\n"
        docstring += f"    {returns}\n"

    return docstring


def fix_docstring_format(docstring: str) -> str:
    """
    Corrige o formato de uma docstring.

    Args:
        docstring: Docstring a ser corrigida

    Returns:
        Docstring corrigida
    """
    lines = docstring.split("\n")

    # Corrigir primeira linha (começar com maiúscula e terminar com ponto)
    if lines and lines[0]:
        # Começar com maiúscula
        if not lines[0][0].isupper():
            lines[0] = lines[0][0].upper() + lines[0][1:]

        # Terminar com ponto
        if not lines[0].endswith("."):
            lines[0] += "."

    # Corrigir seções Args/Returns/Raises
    for i, line in enumerate(lines):
        if line.strip() in ("Args:", "Returns:", "Raises:"):
            # Verificar se a seção está no formato correto
            if i > 0 and lines[i - 1].strip() != "":
                # Adicionar linha em branco antes da seção
                lines.insert(i, "")
                # Ajustar índice
                i += 1

    return "\n".join(lines)


def fix_docstrings_in_file(
    file_path: Path, backup_dir: Path, docstring_info: Dict
) -> bool:
    """
    Corrige docstrings em um arquivo.

    Args:
        file_path: Caminho para o arquivo Python
        backup_dir: Diretório para backup
        docstring_info: Informações sobre docstrings no arquivo

    Returns:
        True se o arquivo foi modificado, False caso contrário
    """
    try:
        with open(file_path, "r") as f:
            content = f.read()

        modified = False

        # Criar backup
        rel_path = file_path.relative_to(backup_dir.parent.parent)
        backup_path = backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Verificar se já temos um backup
        if not backup_path.exists():
            shutil.copy2(file_path, backup_path)

        # Corrigir docstrings não-padrão
        for issue in docstring_info["non_standard_docstrings"]:
            if issue["type"] == "module":
                # Corrigir docstring do módulo
                module_docstring_match = re.match(
                    r'^\s*"""(.*?)"""', content, re.DOTALL
                )
                if module_docstring_match:
                    fixed_docstring = fix_docstring_format(
                        module_docstring_match.group(1)
                    )
                    content = content.replace(
                        module_docstring_match.group(0), f'"""{fixed_docstring}"""'
                    )
                    modified = True

        # Adicionar docstrings faltantes
        for missing in docstring_info["missing_docstrings"]:
            if missing["type"] == "module":
                # Adicionar docstring de módulo
                if not content.strip().startswith('"""'):
                    docstring = f'"""\n{missing["suggestion"]}\n"""\n\n'
                    content = docstring + content
                    modified = True

        # Escrever alterações
        if modified:
            with open(file_path, "w") as f:
                f.write(content)

        return modified

    except Exception as e:
        print(f"Erro ao corrigir docstrings em {file_path}: {e}")
        return False


def generate_docs_report(
    project_root: Path, docstring_analysis: Dict[str, Dict]
) -> None:
    """
    Gera um relatório sobre documentação do projeto.

    Args:
        project_root: Diretório raiz do projeto
        docstring_analysis: Análise de docstrings por arquivo
    """
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    report_file = docs_dir / "documentation_report.md"

    # Calcular estatísticas
    total_files = len(docstring_analysis)
    files_with_module_docstring = sum(
        1 for info in docstring_analysis.values() if info["has_module_docstring"]
    )
    total_classes = sum(len(info["classes"]) for info in docstring_analysis.values())
    classes_with_docstring = sum(
        sum(1 for cls in info["classes"] if cls["has_docstring"])
        for info in docstring_analysis.values()
    )
    total_methods = sum(
        sum(len(cls["methods"]) for cls in info["classes"])
        for info in docstring_analysis.values()
    )
    methods_with_docstring = sum(
        sum(
            sum(1 for method in cls["methods"] if method["has_docstring"])
            for cls in info["classes"]
        )
        for info in docstring_analysis.values()
    )
    total_functions = sum(
        len(info["functions"]) for info in docstring_analysis.values()
    )
    functions_with_docstring = sum(
        sum(1 for func in info["functions"] if func["has_docstring"])
        for info in docstring_analysis.values()
    )

    # Calcular percentuais
    module_docstring_pct = (
        (files_with_module_docstring / total_files) * 100 if total_files > 0 else 0
    )
    class_docstring_pct = (
        (classes_with_docstring / total_classes) * 100 if total_classes > 0 else 0
    )
    method_docstring_pct = (
        (methods_with_docstring / total_methods) * 100 if total_methods > 0 else 0
    )
    function_docstring_pct = (
        (functions_with_docstring / total_functions) * 100 if total_functions > 0 else 0
    )

    # Total de elementos
    total_elements = total_files + total_classes + total_methods + total_functions
    total_documented = (
        files_with_module_docstring
        + classes_with_docstring
        + methods_with_docstring
        + functions_with_docstring
    )
    total_pct = (total_documented / total_elements) * 100 if total_elements > 0 else 0

    with open(report_file, "w") as f:
        f.write("# PepperPy Documentation Report\n\n")
        f.write("## Overview\n\n")
        f.write(
            "This document presents a report on the documentation status of the PepperPy framework.\n\n"
        )

        # Sumário
        f.write("## Summary\n\n")
        f.write("| Element | Total | Documented | Coverage |\n")
        f.write("|---------|-------|------------|----------|\n")
        f.write(
            f"| Modules | {total_files} | {files_with_module_docstring} | {module_docstring_pct:.1f}% |\n"
        )
        f.write(
            f"| Classes | {total_classes} | {classes_with_docstring} | {class_docstring_pct:.1f}% |\n"
        )
        f.write(
            f"| Methods | {total_methods} | {methods_with_docstring} | {method_docstring_pct:.1f}% |\n"
        )
        f.write(
            f"| Functions | {total_functions} | {functions_with_docstring} | {function_docstring_pct:.1f}% |\n"
        )
        f.write(
            f"| **Total** | **{total_elements}** | **{total_documented}** | **{total_pct:.1f}%** |\n\n"
        )

        # Problemas encontrados
        f.write("## Documentation Issues\n\n")
        f.write("### Missing Docstrings\n\n")

        missing_count = sum(
            len(info["missing_docstrings"]) for info in docstring_analysis.values()
        )
        if missing_count > 0:
            f.write("| Type | Name | File | Line |\n")
            f.write("|------|------|------|------|\n")

            for file_path, info in sorted(docstring_analysis.items()):
                for missing in info["missing_docstrings"]:
                    f.write(
                        f"| {missing['type'].capitalize()} | {missing['name']} | {file_path} | {missing['line']} |\n"
                    )
        else:
            f.write("No missing docstrings found.\n\n")

        f.write("\n### Non-standard Docstrings\n\n")

        non_standard_count = sum(
            len(info["non_standard_docstrings"]) for info in docstring_analysis.values()
        )
        if non_standard_count > 0:
            f.write("| Type | Name | File | Line | Issue |\n")
            f.write("|------|------|------|------|-------|\n")

            for file_path, info in sorted(docstring_analysis.items()):
                for issue in info["non_standard_docstrings"]:
                    f.write(
                        f"| {issue['type'].capitalize()} | {issue['name']} | {file_path} | {issue['line']} | {issue['issue']} |\n"
                    )
        else:
            f.write("No non-standard docstrings found.\n\n")

        # Recomendações
        f.write("\n## Recommendations\n\n")
        f.write("1. **Add missing docstrings**: Focus first on public API elements.\n")
        f.write(
            "2. **Standardize existing docstrings**: Follow the Google style guide for Python docstrings.\n"
        )
        f.write(
            "3. **Prioritize modules and classes**: These provide context for the entire codebase.\n"
        )
        f.write(
            "4. **Include usage examples**: Add examples for complex functionality.\n"
        )
        f.write(
            "5. **Keep docstrings updated**: Update documentation when code changes.\n"
        )


def create_doc_template(template_type: str, project_root: Path) -> None:
    """
    Cria um template de documentação.

    Args:
        template_type: Tipo de template (module, class, function)
        project_root: Diretório raiz do projeto
    """
    templates_dir = project_root / "docs" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    if template_type == "module":
        template_content = '''"""
Descrição do módulo.

Este módulo fornece funcionalidades para X, Y e Z.
Pode ser utilizado para realizar operações específicas no sistema.

Examples:
    ```python
    import pepperpy.module as module
    
    result = module.function()
    ```
"""
'''
    elif template_type == "class":
        template_content = '''class MyClass:
    """
    Descrição da classe.
    
    Esta classe implementa funcionalidades para X e Y.
    Utilizada em contextos onde Z é necessário.
    
    Attributes:
        attr1: Descrição do atributo 1.
        attr2: Descrição do atributo 2.
    
    Examples:
        ```python
        obj = MyClass(param1, param2)
        result = obj.method()
        ```
    """
    
    def __init__(self, param1, param2):
        """
        Inicializa a classe.
        
        Args:
            param1: Descrição do parâmetro 1.
            param2: Descrição do parâmetro 2.
        """
        self.attr1 = param1
        self.attr2 = param2
    
    def method(self, param):
        """
        Realiza uma operação.
        
        Args:
            param: Descrição do parâmetro.
            
        Returns:
            Descrição do que é retornado.
            
        Raises:
            ValueError: Se o parâmetro for inválido.
        """
        return result
'''
    elif template_type == "function":
        template_content = '''def my_function(param1, param2, optional_param=None):
    """
    Descrição da função.
    
    Esta função realiza X quando Y acontece.
    Pode ser utilizada em contextos Z.
    
    Args:
        param1: Descrição do parâmetro 1.
        param2: Descrição do parâmetro 2.
        optional_param: Descrição do parâmetro opcional.
            Defaults to None.
    
    Returns:
        Descrição do que é retornado.
        
    Raises:
        ValueError: Se os parâmetros forem inválidos.
        
    Examples:
        ```python
        result = my_function(1, "text")
        ```
    """
    return result
'''

    template_file = templates_dir / f"{template_type}_template.py"
    with open(template_file, "w") as f:
        f.write(template_content)


def create_documentation_guide(project_root: Path) -> None:
    """
    Cria um guia de documentação.

    Args:
        project_root: Diretório raiz do projeto
    """
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    guide_file = docs_dir / "documentation_guide.md"

    guide_content = """# PepperPy Documentation Guide

## Overview

Este guia define os padrões de documentação para o projeto PepperPy. Uma documentação consistente e de alta qualidade é essencial para tornar o framework acessível a novos usuários e facilitar a manutenção por contribuidores.

## Princípios

1. **Clareza**: A documentação deve ser clara, concisa e compreensível.
2. **Completude**: Todos os elementos públicos da API devem ser documentados.
3. **Consistência**: O estilo de documentação deve ser consistente em todo o projeto.
4. **Exemplos**: Exemplos de uso devem ser fornecidos para funcionalidades importantes.
5. **Atualização**: A documentação deve ser mantida atualizada com as mudanças no código.

## Formato de Docstrings

O PepperPy adota o estilo Google para docstrings em Python:

```python
def function(param1, param2):
    \"\"\"
    Breve descrição da função.

    Descrição mais detalhada que explica o que a função faz,
    quando deve ser usada e quaisquer considerações especiais.

    Args:
        param1: Descrição do primeiro parâmetro.
        param2: Descrição do segundo parâmetro. Descrições longas
            podem ser quebradas em várias linhas com indentação.

    Returns:
        Descrição do valor retornado.

    Raises:
        ExceptionType: Descrição das condições que levam à exceção.

    Examples:
        ```python
        result = function("valor1", 42)
        ```
    \"\"\"
```

## Diretrizes por Tipo de Elemento

### Módulos

Todo módulo deve ter uma docstring que:

- Comece com uma breve descrição do propósito do módulo
- Forneça informações sobre as principais classes e funções exportadas
- Inclua exemplos de uso quando apropriado

### Classes

Docstrings de classes devem incluir:

- Descrição geral do propósito da classe
- Atributos públicos
- Exemplos de como instanciar e usar a classe
- Notas sobre herança quando relevante

### Métodos e Funções

Docstrings de métodos e funções devem incluir:

- Breve descrição do que o método/função faz
- Parâmetros (incluindo tipo esperado)
- Valor de retorno (incluindo tipo)
- Exceções que podem ser lançadas
- Exemplos de uso para métodos/funções complexos

## Estrutura da Documentação do Projeto

A documentação do PepperPy é organizada em:

1. **Docstrings no código**: Documentação integrada ao código-fonte
2. **Guias do usuário**: Tutoriais e explicações de conceitos em `/docs/guides/`
3. **Referência da API**: Documentação detalhada da API em `/docs/api/`
4. **Exemplos**: Códigos de exemplo em `/examples/`

## Geração de Documentação

A documentação do PepperPy é gerada automaticamente usando Sphinx. Para gerar a documentação:

```bash
cd docs
make html
```

## Checklist de Documentação

- [ ] Todos os módulos têm docstrings
- [ ] Todas as classes públicas têm docstrings
- [ ] Todos os métodos e funções públicos têm docstrings
- [ ] Parâmetros e retornos estão documentados
- [ ] Exemplos são fornecidos para funcionalidades complexas
- [ ] Docstrings seguem o estilo padrão
- [ ] A documentação está atualizada com o código

## Recursos Adicionais

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [PEP 257 -- Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
"""

    with open(guide_file, "w") as f:
        f.write(guide_content)


def implement_documentation_standardization(
    project_root: Path, backup_dir: Path
) -> None:
    """
    Implementa padronização de documentação.

    Args:
        project_root: Diretório raiz do projeto
        backup_dir: Diretório para backup
    """
    print("Implementando padronização de documentação...")

    # 1. Encontrar arquivos Python
    print("Encontrando arquivos Python...")
    python_files = find_python_files(project_root)
    print(f"Encontrados {len(python_files)} arquivos Python")

    # 2. Criar diretório de backup
    docs_backup_dir = backup_dir / "docs"
    docs_backup_dir.mkdir(parents=True, exist_ok=True)

    # 3. Criar templates de documentação
    print("Criando templates de documentação...")
    create_doc_template("module", project_root)
    create_doc_template("class", project_root)
    create_doc_template("function", project_root)

    # 4. Criar guia de documentação
    print("Criando guia de documentação...")
    create_documentation_guide(project_root)

    # 5. Analisar docstrings nos arquivos
    print("Analisando docstrings...")
    docstring_analysis = {}
    for file_path in python_files:
        rel_path = file_path.relative_to(project_root)
        analysis = extract_docstring_info(file_path)
        docstring_analysis[str(rel_path)] = analysis

    # 6. Corrigir docstrings
    print("Corrigindo docstrings...")
    fixed_files = 0
    for file_path in python_files:
        rel_path = file_path.relative_to(project_root)
        if fix_docstrings_in_file(
            file_path, docs_backup_dir, docstring_analysis[str(rel_path)]
        ):
            fixed_files += 1

    print(f"Corrigidos {fixed_files} arquivos")

    # 7. Gerar relatório
    print("Gerando relatório de documentação...")
    generate_docs_report(project_root, docstring_analysis)

    print(
        "Padronização de documentação concluída! Relatório gerado em docs/documentation_report.md"
    )
