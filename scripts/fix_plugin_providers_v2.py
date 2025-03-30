#!/usr/bin/env python
"""
Script para corrigir a estrutura dos providers PepperPy (versão 2).

Este script identifica e corrige problemas comuns nos providers:
1. Identifica a classe do provider com base no nome do diretório
2. Adiciona tipos de atributos e valores padrão
3. Corrige a estrutura conforme as regras do PepperPy
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).parent.parent

# Mapeamento de tipo de plugin para seus atributos específicos
DOMAIN_ATTRIBUTES = {
    "llm": {
        "model": ("str", "default-model"),
        "temperature": ("float", 0.7),
        "max_tokens": ("int", 1024),
    },
    "embeddings": {
        "model": ("str", "embedding-model"),
        "dimensions": ("int", 1536),
    },
    "rag": {
        "retrieval_type": ("str", "vector"),
        "similarity_threshold": ("float", 0.7),
        "limit": ("int", 10),
    },
    "tts": {
        "voice_id": "str",
        "quality": ("str", "high"),
        "speed": ("float", 1.0),
    },
    "storage": {
        "data_dir": ("str", ".pepperpy/data"),
    },
    "cache": {
        "ttl": ("int", 3600),
    },
}

# Mapeamento de provider específico para seus atributos
PROVIDER_ATTRIBUTES = {
    "openai": {
        "model": ("str", "gpt-3.5-turbo"),
        "base_url": ("str", "https://api.openai.com/v1"),
    },
    "openrouter": {
        "model": ("str", "openai/gpt-3.5-turbo"),
        "base_url": ("str", "https://openrouter.ai/api/v1"),
    },
    "anthropic": {
        "model": ("str", "claude-3-opus-20240229"),
    },
    "cohere": {
        "model": ("str", "command"),
    },
    "playht": {
        "voice_engine": ("str", "PlayHT2.0-turbo"),
    },
    "elevenlabs": {
        "stability": ("float", 0.5),
        "similarity_boost": ("float", 0.75),
    },
}


def find_provider_files() -> List[Path]:
    """Encontra todos os arquivos de provider."""
    return list(ROOT_DIR.glob("plugins/**/provider.py"))


def identify_provider_info(plugin_dir: Path) -> Tuple[str, str, str]:
    """
    Identifica informações do provider com base no diretório.

    Args:
        plugin_dir: Diretório do plugin

    Returns:
        Tuple com (domínio, provider, nome_classe)
    """
    plugin_path = str(plugin_dir.relative_to(ROOT_DIR / "plugins"))
    parts = plugin_path.split("/")

    # Obter o nome do plugin e deduzir o domínio e provider
    plugin_name = parts[0]

    # Detectar o domínio (ex: llm_openai -> llm)
    domain = ""
    provider = ""

    if "_" in plugin_name:
        domain, provider = plugin_name.split("_", 1)
    else:
        # Tentar detectar o domínio por prefixos comuns
        for possible_domain in [
            "llm",
            "embeddings",
            "rag",
            "tts",
            "storage",
            "cache",
            "agents",
            "workflow",
        ]:
            if plugin_name.startswith(possible_domain):
                domain = possible_domain
                provider = plugin_name[len(domain) :]
                break

    if not domain:
        # Último recurso: detectar por categorias no nome do diretório
        for possible_domain in [
            "llm",
            "embeddings",
            "rag",
            "tts",
            "storage",
            "cache",
            "agents",
            "workflow",
        ]:
            if possible_domain in plugin_name:
                domain = possible_domain
                provider = plugin_name.replace(domain, "")
                break

    # Se ainda não temos domínio, usar o primeiro segmento do nome
    if not domain and "_" in plugin_name:
        domain = plugin_name.split("_")[0]
        provider = "_".join(plugin_name.split("_")[1:])

    # Criar nome da classe
    if provider:
        class_name = f"{provider.capitalize()}Provider"
    else:
        class_name = f"{plugin_name.capitalize()}Provider"

    # Alguns domínios têm convenções diferentes de nome
    if domain == "rag":
        class_name = f"{provider.capitalize()}RAGProvider"
    elif domain == "tts":
        class_name = f"{provider.capitalize()}Provider"

    return domain or "unknown", provider or plugin_name, class_name


def find_best_class_in_file(file_path: Path, expected_class_name: str) -> Optional[str]:
    """
    Encontra a melhor classe no arquivo, mesmo que o nome seja diferente do esperado.

    Args:
        file_path: Caminho para o arquivo
        expected_class_name: Nome da classe esperado

    Returns:
        Nome da classe encontrada ou None
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Primeiro, procurar a classe com o nome esperado
    class_pattern = re.compile(
        r"class\s+(" + re.escape(expected_class_name) + r")\s*\("
    )
    match = class_pattern.search(content)
    if match:
        return match.group(1)

    # Se não encontrar, procurar qualquer classe que tenha "Provider" no nome
    class_pattern = re.compile(r"class\s+(\w+Provider)\s*\(")
    matches = class_pattern.findall(content)
    if matches:
        return matches[0]

    # Se ainda não encontrar, procurar qualquer classe
    class_pattern = re.compile(r"class\s+(\w+)\s*\(")
    matches = class_pattern.findall(content)
    if matches:
        return matches[0]

    return None


def fix_provider_file(file_path: Path) -> bool:
    """
    Corrige problemas no arquivo do provider.

    Args:
        file_path: Caminho para o arquivo

    Returns:
        True se o arquivo foi modificado
    """
    try:
        # Obter informações do provider com base no diretório
        plugin_dir = file_path.parent
        domain, provider_name, expected_class_name = identify_provider_info(plugin_dir)

        print(
            f"  ℹ️ Plugin: {plugin_dir.name}, Domínio: {domain}, Provider: {provider_name}"
        )

        # Ler o conteúdo do arquivo
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Verificar se já segue o novo padrão
        if re.search(r"api_key\s*:\s*str", content):
            print("  ✓ O arquivo já segue o novo padrão")
            return False

        # Encontrar a melhor classe no arquivo
        class_name = find_best_class_in_file(file_path, expected_class_name)
        if not class_name:
            print("  ❌ Não foi possível encontrar nenhuma classe no arquivo")
            return False

        print(f"  ✓ Classe encontrada: {class_name}")

        # Extrair padrão de indentação
        indent_match = re.search(r"^( +)", content.split("\n")[1])
        indent = indent_match.group(1) if indent_match else "    "

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

        # Definir atributos para este provider
        attributes = {
            "api_key": "str",
            "client": "Optional[Any]",
        }

        # Adicionar atributos específicos do domínio
        if domain in DOMAIN_ATTRIBUTES:
            for attr, value in DOMAIN_ATTRIBUTES[domain].items():
                attributes[attr] = value

        # Adicionar atributos específicos do provider
        if provider_name in PROVIDER_ATTRIBUTES:
            for attr, value in PROVIDER_ATTRIBUTES[provider_name].items():
                attributes[attr] = value

        # Verificar se o arquivo importa Optional
        needs_optional = "Optional" in attributes.values() and "Optional" not in content

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

        # Construir a nova declaração de classe com atributos
        new_class_declaration = f"class {class_name}"

        # Adicionar os parâmetros da classe
        params_match = re.search(
            r"class\s+" + re.escape(class_name) + r"\s*\(([^)]*)\)", class_declaration
        )
        if params_match:
            new_class_declaration += f"({params_match.group(1)}):"
        else:
            new_class_declaration += "():"

        # Adicionar docstring se existir
        if docstring_match:
            new_class_declaration += f"\n{indent}{docstring_match.group(2)}"
        else:
            new_class_declaration += (
                f'\n{indent}"""Implementação do provider {class_name}."""'
            )

        # Adicionar atributos auto-bound
        new_class_declaration += f"\n\n{indent}# Attributes auto-bound from plugin.yaml com valores padrão como fallback"

        # Adicionar atributos
        for attr, value in attributes.items():
            if attr in configured_attrs:
                # Já configurado no __init__
                if attr == "client":
                    # Alguns atributos têm tratamento especial
                    new_class_declaration += f"\n{indent}{attr}: {value} = None"
                else:
                    new_class_declaration += f"\n{indent}{attr}: {value}"
            elif isinstance(value, tuple):
                # Tupla (tipo, valor padrão)
                attr_type, default_value = value
                if attr_type == "str":
                    new_class_declaration += (
                        f'\n{indent}{attr}: {attr_type} = "{default_value}"'
                    )
                else:
                    new_class_declaration += (
                        f"\n{indent}{attr}: {attr_type} = {default_value}"
                    )
            else:
                # Apenas o tipo
                new_class_declaration += f"\n{indent}{attr}: {value}"

        # Adicionar constantes ou atributos de classe existentes
        class_attrs_pattern = re.compile(r"^\s+([A-Z][A-Z_0-9]*)\s*=\s*", re.MULTILINE)
        for match in class_attrs_pattern.finditer(class_declaration):
            const_name = match.group(1)
            # Encontrar toda a linha de definição da constante
            const_line_pattern = re.compile(f"^\\s+{const_name}\\s*=.*$", re.MULTILINE)
            const_match = const_line_pattern.search(class_declaration)
            if const_match:
                new_class_declaration += f"\n{indent}{const_match.group().strip()}"

        # Substituir a declaração da classe
        new_content = content.replace(class_declaration, new_class_declaration)

        # Garantir que Optional esteja importado se necessário
        if needs_optional:
            # Adicionar importação de Optional se não existir
            if "from typing import" in new_content:
                # Adicionar Optional a uma importação typing existente
                new_content = re.sub(
                    r"from typing import (.*?)\n",
                    lambda m: f"from typing import {m.group(1)}, Optional\n"
                    if "Optional" not in m.group(1)
                    else m.group(0),
                    new_content,
                )
            elif "import " in new_content:
                # Adicionar após as importações existentes
                last_import = re.search(
                    r"^(?:from|import).*?$", new_content, re.MULTILINE
                )
                if last_import:
                    pos = last_import.end()
                    new_content = (
                        new_content[:pos]
                        + "\nfrom typing import Optional, Any"
                        + new_content[pos:]
                    )
            else:
                # Adicionar no início do arquivo
                new_content = "from typing import Optional, Any\n\n" + new_content

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
    """Função principal do script."""
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
