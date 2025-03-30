#!/usr/bin/env python3
"""
Script simples para adicionar valores fixos padrão aos plugins.

Este script identifica e corrige problemas comuns nos plugins:
1. Adiciona valores padrão para atributos fixos (base_url, model, etc)
2. Corrige o entry_point nos plugin.yaml
"""

import re
import sys
from pathlib import Path

import yaml


def fix_plugin(plugin_dir):
    """Corrige problemas no plugin."""
    print(f"Processando {plugin_dir.name}...")
    provider_py = plugin_dir / "provider.py"
    plugin_yaml = plugin_dir / "plugin.yaml"

    if not provider_py.exists() or not plugin_yaml.exists():
        print("  ❌ Arquivos necessários não encontrados")
        return

    # Ler o provider.py
    with open(provider_py) as f:
        provider_content = f.read()

    # Ler o plugin.yaml
    with open(plugin_yaml) as f:
        yaml_content = yaml.safe_load(f)

    # Extrair o nome da classe do provider
    class_pattern = re.compile(r"class\s+(\w+)\s*\(")
    class_match = class_pattern.search(provider_content)
    if not class_match:
        print("  ❌ Não foi possível encontrar a classe do provider")
        return

    class_name = class_match.group(1)

    # Verificar se o entry_point está correto
    entry_point = yaml_content.get("entry_point", "")
    expected_entry_point = f"provider.{class_name}"
    if entry_point != expected_entry_point:
        print(
            f"  ⚠️ entry_point incorreto: {entry_point} (deveria ser {expected_entry_point})"
        )
        yaml_content["entry_point"] = expected_entry_point
        with open(plugin_yaml, "w") as f:
            yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)
        print(f"  ✅ entry_point corrigido para {expected_entry_point}")

    # Verificar os atributos fixos
    domain = yaml_content.get("category", "").lower()
    provider_name = yaml_content.get("provider_type", "").lower()

    # Determinar valores fixos comuns
    fixed_values = {
        "base_url": get_base_url(domain, provider_name),
        "model": get_model_name(domain, provider_name),
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    # Criar regex para procurar atributos
    attrs_pattern = re.compile(r"class\s+\w+.*?def\s+__init__", re.DOTALL)
    attrs_match = attrs_pattern.search(provider_content)
    if not attrs_match:
        print("  ❌ Não foi possível encontrar atributos da classe")
        return

    attrs_section = attrs_match.group(0)

    # Verificar se os atributos fixos já têm valores padrão
    missing_defaults = {}
    for attr, value in fixed_values.items():
        # Padrão para procurar atributos sem valores padrão
        attr_pattern = re.compile(rf"{attr}\s*:\s*\w+(?!\s*=)")
        if attr_pattern.search(attrs_section):
            missing_defaults[attr] = value

    if not missing_defaults:
        print("  ✅ Todos os atributos fixos já têm valores padrão")
        return

    # Adicionar valores padrão aos atributos
    new_attrs_section = attrs_section
    for attr, value in missing_defaults.items():
        # Encontrar a declaração do atributo
        attr_pattern = re.compile(rf"(\s+{attr}\s*:\s*\w+)(?!\s*=)")
        attr_match = attr_pattern.search(new_attrs_section)
        if attr_match:
            formatted_value = format_value(value, attr)
            # Substituir com valor padrão
            replacement = f"{attr_match.group(1)} = {formatted_value}"
            new_attrs_section = new_attrs_section.replace(
                attr_match.group(0), replacement
            )
            print(f"  ✅ Adicionado valor padrão para {attr}: {formatted_value}")

    # Atualizar o conteúdo do arquivo
    new_provider_content = provider_content.replace(attrs_section, new_attrs_section)

    # Verificar se precisamos adicionar código para handle de valores fixos no __init__
    if (
        missing_defaults
        and "# Garantir que valores fixos estão definidos" not in provider_content
    ):
        # Procurar o método __init__
        init_pattern = re.compile(
            r"def\s+__init__\s*\(\s*self\s*,\s*\*\*kwargs\s*:.*?\):\s*[^\n]*\n\s+super\(\)\.__init__\(\*\*kwargs\)\s*\n\s+self\.client\s*=\s*None",
            re.DOTALL,
        )
        init_match = init_pattern.search(new_provider_content)
        if init_match:
            init_code = init_match.group(0)

            # Criar código para garantir valores fixos
            fixed_values_code = "\n        # Garantir que valores fixos estão definidos - usar kwargs, depois os padrões da classe\n"
            for attr in missing_defaults.keys():
                fixed_values_code += f"        if '{attr}' in kwargs:\n"
                fixed_values_code += f"            self.{attr} = kwargs['{attr}']\n"

            # Inserir após "self.client = None"
            new_init_code = init_code + fixed_values_code
            new_provider_content = new_provider_content.replace(
                init_code, new_init_code
            )
            print("  ✅ Adicionado código para handle de valores fixos no __init__")

    # Salvar o arquivo atualizado
    with open(provider_py, "w") as f:
        f.write(new_provider_content)

    # Garantir que os valores padrão também estão no plugin.yaml
    default_config = yaml_content.get("default_config", {})
    if default_config is None:
        default_config = {}
        yaml_content["default_config"] = default_config

    # Adicionar valores padrão ao default_config
    yaml_updated = False
    for attr, value in missing_defaults.items():
        if attr not in default_config:
            default_config[attr] = value
            yaml_updated = True
            print(f"  ✅ Adicionado {attr} ao default_config no plugin.yaml")

    # Salvar o plugin.yaml atualizado
    if yaml_updated:
        with open(plugin_yaml, "w") as f:
            yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)


def get_base_url(domain, provider_name):
    """Retorna uma base_url padrão para o provider."""
    known_providers = {
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "azure": "https://api.cognitive.microsoft.com",
        "cohere": "https://api.cohere.ai/v1",
        "huggingface": "https://api-inference.huggingface.co",
        "google": "https://generativelanguage.googleapis.com/v1",
    }

    for name, url in known_providers.items():
        if name in provider_name:
            return url

    return f"https://api.example.com/{domain}/v1"


def get_model_name(domain, provider_name):
    """Retorna um nome de modelo padrão para o provider."""
    known_models = {
        "openai": "gpt-3.5-turbo",
        "openrouter": "openai/gpt-3.5-turbo",
        "anthropic": "claude-2",
        "cohere": "command",
        "google": "gemini-pro",
    }

    for name, model in known_models.items():
        if name in provider_name:
            return model

    if domain == "llm":
        return "text-model"
    elif domain == "embeddings":
        return "embedding-model"
    else:
        return "default-model"


def format_value(value, attr):
    """Formata um valor de acordo com seu tipo provável."""
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, float):
        return str(value)
    elif isinstance(value, int):
        return str(value)
    elif attr in ["temperature", "top_p"]:
        return "0.7"
    elif attr in ["max_tokens", "top_k"]:
        return "1024"
    return "None"


def main():
    """Função principal."""
    plugins_dir = Path("plugins")

    if not plugins_dir.exists():
        print(f"Erro: Diretório de plugins não encontrado: {plugins_dir}")
        sys.exit(1)

    # Ler plugins_refactored.txt para pular plugins já processados
    processed_plugins = set()
    if Path("plugins_refactored.txt").exists():
        with open("plugins_refactored.txt") as f:
            for line in f:
                processed_plugins.add(line.strip())

    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue

        if plugin_dir.name in processed_plugins:
            print(f"Pulando {plugin_dir.name} (já processado)")
            continue

        fix_plugin(plugin_dir)

        # Marcar como processado
        with open("plugins_refactored.txt", "a") as f:
            f.write(f"{plugin_dir.name}\n")


if __name__ == "__main__":
    main()
