#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gerador de artigos usando PepperPy.

Purpose:
    Demonstrar como criar um gerador de artigos
    estruturado a partir de um tópico, utilizando o framework PepperPy
    para orquestrar o fluxo de trabalho.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/content_generation/article_generator.py
"""

import asyncio
import os
import random
from typing import Optional, Union

from pepperpy.apps import ContentApp


def generate_fake_topic() -> str:
    """Gera um tópico fake para o artigo.

    Returns:
        Tópico fake
    """
    topics = [
        "Inteligência Artificial na Educação",
        "Blockchain e Criptomoedas",
        "Computação Quântica",
        "Cidades Inteligentes",
        "Realidade Virtual e Aumentada",
        "Veículos Autônomos",
        "Energia Renovável",
        "Medicina Personalizada",
        "Exploração Espacial",
        "Robótica Avançada",
    ]

    return random.choice(topics)


async def generate_article(
    topic: str,
    depth: str = "detailed",
    language: str = "pt",
    style: str = "journalistic",
    length: str = "medium",
    output_format: str = "markdown",
    output_path: Optional[str] = None,
    include_metadata: bool = False,
) -> Union[str, None]:
    """Gera um artigo sobre um tópico.

    Args:
        topic: Tópico do artigo
        depth: Profundidade da análise (basic, detailed, comprehensive)
        language: Idioma do conteúdo
        style: Estilo de escrita (academic, journalistic, blog)
        length: Tamanho do artigo (short, medium, long)
        output_format: Formato de saída (markdown, html, text)
        output_path: Caminho para salvar o artigo (opcional)
        include_metadata: Incluir metadados no artigo

    Returns:
        Caminho do arquivo gerado ou conteúdo do artigo, ou None em caso de erro
    """
    # Criar aplicação de geração de conteúdo com uma única linha
    app = ContentApp(name="article_generator")

    # Configurar a aplicação com uma API fluente
    app.configure(
        depth=depth,
        language=language,
        style=style,
        length=length,
        output_format=output_format,
        include_metadata=include_metadata,
    )

    # Se um caminho de saída foi especificado, configurar
    if output_path:
        app.set_output_path(output_path)

    # Gerar artigo com uma única chamada
    result = await app.generate_article(topic)

    # Retornar o caminho do arquivo ou o conteúdo
    return result.output_path if output_path else result.content


async def main():
    """Executa o exemplo de geração de artigos."""
    print("=== Gerador de Artigos com PepperPy ===")
    print("Este exemplo demonstra como gerar artigos estruturados")
    print("a partir de um tópico usando o PepperPy.")

    # Definir configurações para diferentes tipos de artigos
    configurations = [
        {
            "name": "Básico",
            "config": {
                "depth": "basic",
                "style": "blog",
                "length": "short",
                "include_metadata": False,
            },
        },
        {
            "name": "Padrão",
            "config": {
                "depth": "detailed",
                "style": "journalistic",
                "length": "medium",
                "include_metadata": False,
            },
        },
        {
            "name": "Detalhado",
            "config": {
                "depth": "comprehensive",
                "style": "academic",
                "length": "long",
                "include_metadata": True,
            },
        },
    ]

    # Gerar artigos com diferentes configurações
    for i, config_item in enumerate(configurations):
        # Gerar tópico fake
        topic = generate_fake_topic()

        # Obter configuração
        config_name = config_item["name"]
        config = config_item["config"]

        print(f"\n--- Gerando Artigo {i + 1}: {config_name} ---")
        print(f"Tópico: {topic}")
        print(f"Configuração: {config}")

        # Gerar artigo
        output_path = f"{topic.lower().replace(' ', '_')}_article_{i + 1}.md"
        article_path = await generate_article(
            topic=topic, **config, output_format="markdown", output_path=output_path
        )

        if article_path:
            print("Artigo gerado com sucesso!")
            print(f"Salvo em: {article_path}")

            # Mostrar primeiras linhas do artigo
            if os.path.exists(article_path):
                with open(article_path, "r") as f:
                    content = f.read(500)  # Ler primeiros 500 caracteres
                print("\nPrimeiras linhas do artigo:")
                print("-" * 50)
                print(content + "...")
                print("-" * 50)
        else:
            print("Erro ao gerar artigo.")

        # Pausa entre gerações
        if i < len(configurations) - 1:
            await asyncio.sleep(1)

    print("\n=== Geração de Artigos Concluída ===")


if __name__ == "__main__":
    asyncio.run(main())
