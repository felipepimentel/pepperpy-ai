#!/usr/bin/env python
"""
Script para atualizar os providers do PepperPy para usar o padrão recomendado
com atributos fixos declarados como atributos de classe.

Este script identifica os providers que seguem o padrão antigo e os atualiza
para o novo padrão.
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).parent.parent

# Valores fixos que devem ser definidos como atributos de classe
COMMON_FIXED_VALUES = {
    "api_key": None,
    "model": "str",
    "temperature": "float",
    "max_tokens": "int",
    "base_url": "str",
    "embeddings_model": "str",
    "dimensions": "int",
}

# Mapeamento de providers para seus valores fixos e tipos
PROVIDER_FIXED_VALUES: Dict[str, Dict[str, Tuple[str, Any]]] = {
    "OpenAIProvider": {
        "model": ("str", "gpt-3.5-turbo"),
        "temperature": ("float", 0.7),
        "max_tokens": ("int", 1024),
    },
    "OpenRouterProvider": {
        "model": ("str", "openai/gpt-3.5-turbo"),
        "base_url": ("str", "https://openrouter.ai/api/v1"),
        "temperature": ("float", 0.7),
        "max_tokens": ("int", 1024),
    },
    "AnthropicProvider": {
        "model": ("str", "claude-3-opus-20240229"),
        "temperature": ("float", 0.7),
        "max_tokens": ("int", 1024),
    },
    "OpenAIEmbeddingProvider": {
        "model": ("str", "text-embedding-3-small"),
    },
    "OpenRouterEmbeddingProvider": {
        "model": ("str", "openai/text-embedding-3-small"),
        "base_url": ("str", "https://openrouter.ai/api/v1"),
    },
}

# Extensões de arquivo a serem processadas
EXTENSIONS = [".py"]


def find_provider_files() -> List[Path]:
    """
    Encontra todos os arquivos de provider no projeto.

    Returns:
        Lista de caminhos para arquivos de provider
    """
    provider_files = []

    for ext in EXTENSIONS:
        # Buscar em plugins/*/provider.py
        provider_files.extend(ROOT_DIR.glob(f"plugins/**/provider{ext}"))

    return provider_files


def extract_provider_class(file_path: Path) -> Optional[ast.ClassDef]:
    """
    Extrai a classe de provider de um arquivo.

    Args:
        file_path: Caminho para o arquivo

    Returns:
        Definição da classe ou None se não encontrada
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Verificar se é uma classe de provider
                if "Provider" in node.name:
                    return node

        return None
    except SyntaxError:
        print(f"Erro de sintaxe no arquivo {file_path}")
        return None


def update_provider_file(file_path: Path, provider_class: ast.ClassDef) -> bool:
    """
    Atualiza um arquivo de provider para usar o novo padrão.

    Args:
        file_path: Caminho para o arquivo
        provider_class: Definição da classe de provider

    Returns:
        True se o arquivo foi atualizado, False caso contrário
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Verificar se o arquivo já segue o novo padrão
    class_attrs_pattern = r"class\s+[^(]+\([^)]+\):\s*[^\n]*\n(\s+[^\n]*\n)*"
    if re.search(r"model:\s*str\s*=", content):
        print(f"O arquivo {file_path} já segue o novo padrão")
        return False

    # Obter o provider específico
    provider_values = PROVIDER_FIXED_VALUES.get(provider_class.name, {})

    # Detectar indentação do arquivo
    indent_match = re.search(r"^\s+", content.split("\n")[1])
    indent = indent_match.group(0) if indent_match else "    "

    # Atualizar o conteúdo
    updated = False

    # Encontrar onde adicionar os atributos de classe
    class_def_pattern = f"class {provider_class.name}\\([^)]+\\):"
    class_match = re.search(class_def_pattern, content)

    if not class_match:
        print(
            f"Não foi possível encontrar a classe {provider_class.name} em {file_path}"
        )
        return False

    # Encontrar a primeira linha após a docstring da classe
    class_start = class_match.end()
    doc_start = content.find('"""', class_start)

    if doc_start > 0:
        doc_end = content.find('"""', doc_start + 3)
        if doc_end > 0:
            insert_point = doc_end + 3
        else:
            insert_point = class_start
    else:
        insert_point = class_start

    # Encontrar o próximo método ou fim da classe
    next_def = content.find("def ", insert_point)

    if next_def > 0:
        # Adicionar os atributos de classe antes do primeiro método
        attrs_text = "\n"

        # Se provider_values estiver vazio, usar valores padrão
        if not provider_values:
            print(
                f"Não encontrei valores fixos para {provider_class.name}, usando defaults"
            )

        # Adicionar comentário
        attrs_text += f"{indent}# Attributes auto-bound from plugin.yaml com valores padrão como fallback\n"

        # Sempre adicionar api_key
        attrs_text += f"{indent}api_key: str\n"

        # Adicionar outros atributos fixos
        for attr, (attr_type, default_value) in provider_values.items():
            if default_value is not None:
                # Se o valor for string, adicionar aspas
                if attr_type == "str" and not isinstance(default_value, bool):
                    attrs_text += f'{indent}{attr}: {attr_type} = "{default_value}"'
                else:
                    attrs_text += f"{indent}{attr}: {attr_type} = {default_value}"

                # Adicionar comentário
                if attr == "base_url":
                    attrs_text += "  # Valor fixo como fallback"
                elif attr == "model":
                    attrs_text += "  # Fallback padrão"
                else:
                    attrs_text += "  # Valor padrão sensato"

                attrs_text += "\n"

        # Verificar se o provider tem client
        if "self.client" in content:
            client_type = (
                "AsyncOpenAI" if "AsyncOpenAI" in content else "httpx.AsyncClient"
            )
            attrs_text += f"{indent}client: Optional[{client_type}] = None\n"

        # Inserir os atributos
        updated_content = content[:next_def] + attrs_text + content[next_def:]

        # Verificar se precisamos atualizar o __init__ para remover definições redundantes
        init_pattern = r"def __init__\(self[^)]*\)[^:]*:(.*?)def "
        init_match = re.search(init_pattern, updated_content, re.DOTALL)

        if init_match:
            init_body = init_match.group(1)

            # Remover atribuições redundantes
            for attr in provider_values.keys():
                attr_pattern = rf"self\.{attr}\s*=\s*kwargs\.get\(['\"{attr}['\"](.*?)(?:\n{indent}|$)"
                init_body = re.sub(attr_pattern, "", init_body, flags=re.DOTALL)

            # Atualizar o __init__
            updated_content = updated_content.replace(init_match.group(1), init_body)

        # Salvar o arquivo atualizado
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        print(f"Atualizado: {file_path}")
        return True

    return False


def main():
    """
    Função principal do script.
    """
    provider_files = find_provider_files()
    print(f"Encontrei {len(provider_files)} arquivos de provider")

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for file_path in provider_files:
        print(f"\nProcessando {file_path}...")

        provider_class = extract_provider_class(file_path)

        if provider_class:
            try:
                if update_provider_file(file_path, provider_class):
                    updated_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"Erro ao processar {file_path}: {e}")
                error_count += 1
        else:
            print(f"Não foi possível encontrar a classe do provider em {file_path}")
            error_count += 1

    print("\nResumo:")
    print(f"  - {updated_count} arquivos atualizados")
    print(f"  - {skipped_count} arquivos já no padrão ou ignorados")
    print(f"  - {error_count} arquivos com erros")


if __name__ == "__main__":
    main()
