#!/usr/bin/env python
"""
Script para corrigir a estrutura dos providers PepperPy.

Este script identifica e corrige problemas comuns nos providers:
1. Indentação incorreta no __init__
2. Falta de tipos em atributos
3. Valores fixos definidos no __init__ em vez de como atributos de classe
4. Uso incorreto de fallbacks para os valores fixos
"""

import re
from pathlib import Path
from typing import List, Optional

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).parent.parent

# Valores fixos comuns com seus tipos
COMMON_ATTRIBUTES = {
    "api_key": "str",
    "model": ("str", "default-model"),
    "base_url": "str",
    "temperature": ("float", 0.7),
    "max_tokens": ("int", 1024),
    "user_id": "str",
    "client": "Optional[Any]",
}

# Mapeamento específico de providers
PROVIDER_ATTRIBUTES = {
    "OpenAIProvider": {
        "model": ("str", "gpt-3.5-turbo"),
        "client": "Optional[AsyncOpenAI]",
    },
    "OpenRouterProvider": {
        "model": ("str", "openai/gpt-3.5-turbo"),
        "base_url": ("str", "https://openrouter.ai/api/v1"),
        "client": "Optional[httpx.AsyncClient]",
    },
    "PlayHTProvider": {
        "voice_engine": ("str", "PlayHT2.0-turbo"),
        "quality": ("str", "premium"),
        "speed": ("float", 1.0),
    },
}


def find_provider_files() -> List[Path]:
    """
    Encontra todos os arquivos de provider no projeto.

    Returns:
        Lista de caminhos para arquivos de provider
    """
    return list(ROOT_DIR.glob("plugins/**/provider.py"))


def extract_class_name(file_content: str) -> Optional[str]:
    """
    Extrai o nome da classe do provider do conteúdo do arquivo.

    Args:
        file_content: Conteúdo do arquivo

    Returns:
        Nome da classe ou None se não encontrado
    """
    # Regex para encontrar a declaração da classe
    class_pattern = re.compile(r"class\s+(\w+)\s*\(")

    match = class_pattern.search(file_content)
    if match:
        return match.group(1)

    return None


def extract_imports(file_content: str) -> List[str]:
    """
    Extrai as importações do arquivo.

    Args:
        file_content: Conteúdo do arquivo

    Returns:
        Lista de importações
    """
    imports = []

    # Encontrar linhas de importação
    import_pattern = re.compile(r"(from\s+.*?import\s+.*|import\s+.*)", re.MULTILINE)

    for match in import_pattern.finditer(file_content):
        imports.append(match.group(1))

    return imports


def needs_optional_import(file_content: str) -> bool:
    """
    Verifica se o arquivo precisa de importação de Optional.

    Args:
        file_content: Conteúdo do arquivo

    Returns:
        True se precisar da importação
    """
    return "Optional" in file_content and "Optional" not in extract_imports(
        file_content
    )


def fix_provider_file(file_path: Path) -> bool:
    """
    Corrige problemas no arquivo do provider.

    Args:
        file_path: Caminho para o arquivo

    Returns:
        True se o arquivo foi modificado
    """
    try:
        # Ler o conteúdo do arquivo
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Extrair o nome da classe
        class_name = extract_class_name(content)
        if not class_name:
            print(
                f"  ❌ Não foi possível encontrar a classe do provider em {file_path}"
            )
            return False

        print(f"  ✓ Classe encontrada: {class_name}")

        # Verificar se já segue o novo padrão
        if re.search(r"api_key\s*:\s*str", content):
            print("  ✓ O arquivo já segue o novo padrão")
            return False

        # Importações
        imports = extract_imports(content)

        # Adicionar Optional se necessário
        needs_optional = needs_optional_import(content)
        has_typing_import = any("from typing import" in imp for imp in imports)

        # Encontrar a declaração da classe
        class_pattern = re.compile(
            r"(class\s+" + re.escape(class_name) + r"\s*\([^)]*\):.*?)(?=\s+def\s+|$)",
            re.DOTALL,
        )
        class_match = class_pattern.search(content)

        if not class_match:
            print(
                f"  ❌ Não foi possível encontrar a declaração completa da classe {class_name}"
            )
            return False

        class_declaration = class_match.group(1)

        # Encontrar a docstring da classe
        docstring_pattern = re.compile(
            r"(class\s+"
            + re.escape(class_name)
            + r"\s*\([^)]*\):\s*)(\"\"\".*?\"\"\"\s*)",
            re.DOTALL,
        )
        docstring_match = docstring_pattern.search(content)

        # Definir valores de atributos para esta classe
        provider_attributes = {}

        # Adicionar atributos comuns
        for attr, type_info in COMMON_ATTRIBUTES.items():
            if isinstance(type_info, tuple):
                attr_type, default_value = type_info
                provider_attributes[attr] = (attr_type, default_value)
            else:
                provider_attributes[attr] = (type_info, None)

        # Adicionar atributos específicos do provider
        if class_name in PROVIDER_ATTRIBUTES:
            for attr, type_info in PROVIDER_ATTRIBUTES[class_name].items():
                if isinstance(type_info, tuple):
                    attr_type, default_value = type_info
                    provider_attributes[attr] = (attr_type, default_value)
                else:
                    provider_attributes[attr] = (type_info, None)

        # Extrair padrão de indentação
        indent_match = re.search(r"^( +)", content.split("\n")[1])
        indent = indent_match.group(1) if indent_match else "    "

        # Construir a nova declaração de classe com atributos
        new_class_declaration = f"class {class_name}"

        # Adicionar os parâmetros da classe
        params_match = re.search(
            r"class\s+" + re.escape(class_name) + r"\s*\(([^)]*)\)", class_declaration
        )
        if params_match:
            new_class_declaration += f"({params_match.group(1)}):"
        else:
            new_class_declaration += "(AbstractProvider):"  # Fallback

        # Adicionar docstring se existir
        if docstring_match:
            new_class_declaration += f"\n{indent}{docstring_match.group(2)}"
        else:
            new_class_declaration += (
                f'\n{indent}"""Implementação do provider {class_name}."""'
            )

        # Adicionar atributos auto-bound
        new_class_declaration += f"\n\n{indent}# Attributes auto-bound from plugin.yaml com valores padrão como fallback"

        # Identificar atributos que já estão sendo configurados no __init__
        init_pattern = re.compile(
            r"def\s+__init__\s*\([^)]*\).*?(?=\s+(?:@|def)\s+|$)", re.DOTALL
        )
        init_match = init_pattern.search(content)

        configured_attrs = set()
        if init_match:
            init_body = init_match.group(0)
            # Encontrar atribuições no __init__
            attr_pattern = re.compile(r"self\.(\w+)\s*=\s*")
            configured_attrs = set(attr_pattern.findall(init_body))

        # Adicionar atributos
        for attr, (attr_type, default_value) in provider_attributes.items():
            if attr in configured_attrs:
                # Adicionar sem valor padrão se já configurado no __init__
                if attr == "client":
                    new_class_declaration += f"\n{indent}{attr}: {attr_type} = None"
                else:
                    new_class_declaration += f"\n{indent}{attr}: {attr_type}"
            elif default_value is not None:
                # Adicionar com valor padrão
                if attr_type == "str":
                    new_class_declaration += (
                        f'\n{indent}{attr}: {attr_type} = "{default_value}"'
                    )
                else:
                    new_class_declaration += (
                        f"\n{indent}{attr}: {attr_type} = {default_value}"
                    )
            else:
                # Adicionar sem valor padrão
                new_class_declaration += f"\n{indent}{attr}: {attr_type}"

        # Adicionar constantes ou atributos de classe existentes
        class_attrs_pattern = re.compile(r"^\s+([A-Z][A-Z_0-9]*)\s*=\s*", re.MULTILINE)
        for match in class_attrs_pattern.finditer(class_declaration):
            const_name = match.group(1)
            # Encontrar toda a linha de definição da constante
            const_line_pattern = re.compile(f"^\s+{const_name}\s*=.*$", re.MULTILINE)
            const_match = const_line_pattern.search(class_declaration)
            if const_match:
                new_class_declaration += f"\n{indent}{const_match.group().strip()}"

        # Substituir a declaração da classe
        new_content = content.replace(class_declaration, new_class_declaration)

        # Se precisar de Optional na typagem, adicionar a importação
        if needs_optional and not has_typing_import:
            # Encontrar onde adicionar a importação
            typing_import = "from typing import Any, Optional"

            if "from typing import" in new_content:
                # Adicionar Optional a uma importação existente de typing
                new_content = re.sub(
                    r"from typing import (.*?)\n",
                    lambda m: f"from typing import {m.group(1)}, Optional\n"
                    if "Optional" not in m.group(1)
                    else m.group(0),
                    new_content,
                )
            else:
                # Adicionar uma nova importação
                last_import_match = re.search(
                    r"^(import|from)\s+.*?$", new_content, re.MULTILINE
                )
                if last_import_match:
                    last_import_pos = last_import_match.end()
                    new_content = (
                        new_content[:last_import_pos]
                        + f"\n{typing_import}"
                        + new_content[last_import_pos:]
                    )
                else:
                    # Se não encontrar outras importações, adicionar no início
                    new_content = f"{typing_import}\n\n" + new_content

        # Atualizar o conteúdo do arquivo
        if content != new_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  ✅ Arquivo atualizado: {file_path}")
            return True
        else:
            print("  ✓ Nenhuma alteração necessária")
            return False

    except Exception as e:
        print(f"  ❌ Erro ao processar {file_path}: {e!s}")
        return False


def main():
    """
    Função principal do script.
    """
    provider_files = find_provider_files()
    print(f"Encontrados {len(provider_files)} arquivos de provider")

    updated = 0
    skipped = 0
    error = 0

    for file_path in provider_files:
        print(f"\nProcessando {file_path.relative_to(ROOT_DIR)}...")
        try:
            if fix_provider_file(file_path):
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ❌ Erro não tratado: {e!s}")
            error += 1

    print("\nResumo:")
    print(f"  - {updated} arquivos atualizados")
    print(f"  - {skipped} arquivos ignorados")
    print(f"  - {error} arquivos com erros")


if __name__ == "__main__":
    main()
