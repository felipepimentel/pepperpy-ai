#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de teste para verificar o funcionamento básico do módulo de composição.

Este script importa diretamente os módulos de composição sem depender de outros
módulos do framework.
"""

import asyncio
import importlib.util
import os
import sys


# Função para importar um módulo diretamente do arquivo
def import_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Could not load spec for {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    if spec.loader is None:
        raise ImportError(f"Could not load module {module_name} from {file_path}")
    spec.loader.exec_module(module)
    return module


# Importar os módulos necessários diretamente dos arquivos
base_path = os.path.abspath("pepperpy/core/composition")
types_module = import_module_from_file(
    "types_module", os.path.join(base_path, "types.py")
)
components_module = import_module_from_file(
    "components_module", os.path.join(base_path, "components.py")
)
public_module = import_module_from_file(
    "public_module", os.path.join(base_path, "public.py")
)

# Extrair as classes e funções necessárias
Sources = components_module.Sources
Processors = components_module.Processors
Outputs = components_module.Outputs
compose = public_module.compose
compose_parallel = public_module.compose_parallel


async def test_components():
    """Testa a criação de componentes."""
    print("\n=== Teste de Criação de Componentes ===")

    # Testar a criação de fontes
    try:
        text_source = Sources.text("Este é um texto de exemplo.")
        print(f"Fonte de texto criada: {text_source}")

        file_source = Sources.file("example.txt")
        print(f"Fonte de arquivo criada: {file_source}")

        rss_source = Sources.rss("https://example.com/rss")
        print(f"Fonte RSS criada: {rss_source}")
    except Exception as e:
        print(f"Erro ao criar fontes: {e}")

    # Testar a criação de processadores
    try:
        summarize_processor = Processors.summarize(max_length=100)
        print(f"Processador de resumo criado: {summarize_processor}")

        translate_processor = Processors.translate(target_language="pt")
        print(f"Processador de tradução criado: {translate_processor}")

        keywords_processor = Processors.extract_keywords(max_keywords=5)
        print(f"Processador de extração de palavras-chave criado: {keywords_processor}")
    except Exception as e:
        print(f"Erro ao criar processadores: {e}")

    # Testar a criação de saídas
    try:
        file_output = Outputs.file("output.txt")
        print(f"Saída de arquivo criada: {file_output}")

        podcast_output = Outputs.podcast("podcast.mp3", voice="en")
        print(f"Saída de podcast criada: {podcast_output}")
    except Exception as e:
        print(f"Erro ao criar saídas: {e}")


async def main():
    """Função principal."""
    print("=== Teste do Módulo de Composição ===")

    # Testar a criação de componentes
    await test_components()

    print("\nTestes concluídos!")


if __name__ == "__main__":
    asyncio.run(main())
