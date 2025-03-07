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
from datetime import datetime
from typing import Any, Dict, Optional

from pepperpy.core.apps import ContentApp


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


class ArticleGenerator(ContentApp):
    """Gerador de artigos para demonstração."""

    def __init__(self, name: str = "article_generator"):
        """Inicializar gerador de artigos.

        Args:
            name: Nome do gerador
        """
        super().__init__(name=name)
        self.output_dir = "examples/outputs/content_generation"
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_article(
        self,
        topic: str,
        depth: str = "detailed",
        language: str = "pt",
        style: str = "journalistic",
        length: str = "medium",
        output_format: str = "markdown",
        output_path: Optional[str] = None,
        include_metadata: bool = False,
    ) -> Dict[str, Any]:
        """Gera um artigo sobre um tópico.

        Args:
            topic: Tópico do artigo
            depth: Profundidade do artigo (basic, detailed, comprehensive)
            language: Idioma do artigo
            style: Estilo do artigo (journalistic, academic, informal)
            length: Tamanho do artigo (short, medium, long)
            output_format: Formato de saída (markdown, html, text)
            output_path: Caminho para salvar o artigo
            include_metadata: Incluir metadados no artigo

        Returns:
            Informações sobre o artigo gerado
        """
        print(f"Gerando artigo sobre '{topic}'")
        print(
            f"Configurações: {depth=}, {language=}, {style=}, {length=}, {output_format=}"
        )

        # Simular tempo de geração
        await asyncio.sleep(1)

        # Gerar título
        title = f"{topic}: Uma Análise {self._get_depth_adjective(depth)}"

        # Gerar conteúdo simulado
        content = self._generate_fake_content(topic, depth, style, length)

        # Definir caminho de saída
        if not output_path:
            safe_topic = (
                topic.lower()
                .replace(" ", "_")
                .replace("ç", "c")
                .replace("ã", "a")
                .replace("é", "e")
            )
            output_path = os.path.join(
                self.output_dir,
                f"artigo_{safe_topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{self._get_extension(output_format)}",
            )

        # Formatar conteúdo
        formatted_content = self._format_content(
            title, content, output_format, include_metadata
        )

        # Salvar artigo
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)

        print(f"Artigo gerado e salvo em: {output_path}")

        # Retornar informações
        return {
            "topic": topic,
            "title": title,
            "output_path": output_path,
            "word_count": len(content.split()),
            "format": output_format,
            "language": language,
            "generated_at": datetime.now().isoformat(),
        }

    def _get_depth_adjective(self, depth: str) -> str:
        """Obtém um adjetivo baseado na profundidade.

        Args:
            depth: Profundidade do artigo

        Returns:
            Adjetivo correspondente
        """
        if depth == "basic":
            return "Introdutória"
        elif depth == "detailed":
            return "Detalhada"
        elif depth == "comprehensive":
            return "Abrangente"
        else:
            return "Geral"

    def _get_extension(self, output_format: str) -> str:
        """Obtém a extensão de arquivo baseada no formato.

        Args:
            output_format: Formato de saída

        Returns:
            Extensão de arquivo
        """
        if output_format == "markdown":
            return "md"
        elif output_format == "html":
            return "html"
        else:
            return "txt"

    def _generate_fake_content(
        self, topic: str, depth: str, style: str, length: str
    ) -> str:
        """Gera conteúdo fake para o artigo.

        Args:
            topic: Tópico do artigo
            depth: Profundidade do artigo
            style: Estilo do artigo
            length: Tamanho do artigo

        Returns:
            Conteúdo gerado
        """
        # Determinar número de parágrafos baseado no tamanho
        if length == "short":
            num_paragraphs = 3
        elif length == "medium":
            num_paragraphs = 5
        else:  # long
            num_paragraphs = 8

        # Gerar parágrafos
        paragraphs = []

        # Introdução
        paragraphs.append(
            f"Este artigo aborda o tema {topic}, explorando seus principais aspectos e implicações. A seguir, apresentamos uma análise {self._get_depth_adjective(depth).lower()} sobre o assunto."
        )

        # Corpo
        for i in range(1, num_paragraphs - 1):
            paragraphs.append(
                f"Parágrafo {i + 1}: Continuando nossa análise sobre {topic}, podemos observar diversos aspectos relevantes. "
                + "Este é um texto simulado para demonstração do gerador de artigos. "
                * 3
            )

        # Conclusão
        paragraphs.append(
            f"Em conclusão, {topic} representa um campo de estudo fascinante com diversas aplicações e implicações. Este artigo buscou apresentar uma visão {self._get_depth_adjective(depth).lower()} sobre o tema, destacando seus principais aspectos."
        )

        return "\n\n".join(paragraphs)

    def _format_content(
        self, title: str, content: str, output_format: str, include_metadata: bool
    ) -> str:
        """Formata o conteúdo do artigo.

        Args:
            title: Título do artigo
            content: Conteúdo do artigo
            output_format: Formato de saída
            include_metadata: Incluir metadados

        Returns:
            Conteúdo formatado
        """
        if output_format == "markdown":
            formatted = f"# {title}\n\n"

            if include_metadata:
                formatted += "---\n"
                formatted += f"date: {datetime.now().strftime('%Y-%m-%d')}\n"
                formatted += "author: PepperPy Article Generator\n"
                formatted += "---\n\n"

            formatted += content

        elif output_format == "html":
            formatted = f"<!DOCTYPE html>\n<html>\n<head>\n<title>{title}</title>\n"

            if include_metadata:
                formatted += f'<meta name="date" content="{datetime.now().strftime("%Y-%m-%d")}">\n'
                formatted += (
                    '<meta name="author" content="PepperPy Article Generator">\n'
                )

            formatted += "</head>\n<body>\n"
            formatted += f"<h1>{title}</h1>\n\n"

            # Converter parágrafos para HTML
            for paragraph in content.split("\n\n"):
                formatted += f"<p>{paragraph}</p>\n\n"

            formatted += "</body>\n</html>"

        else:  # text
            formatted = f"{title.upper()}\n\n"

            if include_metadata:
                formatted += f"Data: {datetime.now().strftime('%Y-%m-%d')}\n"
                formatted += "Autor: PepperPy Article Generator\n\n"

            formatted += content

        return formatted


async def main():
    """Função principal."""
    print("=== Gerador de Artigos PepperPy ===")
    print("Este exemplo demonstra como gerar artigos usando o PepperPy.")

    # Criar gerador de artigos
    generator = ArticleGenerator()

    # Configurações para diferentes tipos de artigos
    article_configs = [
        {
            "name": "Artigo Básico",
            "config": {
                "depth": "basic",
                "style": "journalistic",
                "length": "short",
                "output_format": "markdown",
            },
        },
        {
            "name": "Artigo Detalhado",
            "config": {
                "depth": "detailed",
                "style": "academic",
                "length": "medium",
                "output_format": "html",
                "include_metadata": True,
            },
        },
        {
            "name": "Artigo Abrangente",
            "config": {
                "depth": "comprehensive",
                "style": "informal",
                "length": "long",
                "output_format": "text",
            },
        },
    ]

    # Gerar artigos com diferentes configurações
    for i, config_item in enumerate(article_configs):
        # Obter configuração
        config_name = config_item["name"]
        config = config_item["config"]

        # Gerar tópico
        topic = generate_fake_topic()

        print(f"\n--- Gerando {config_name} ---")
        print(f"Tópico: {topic}")

        # Gerar artigo
        result = await generator.generate_article(topic=topic, **config)

        print(f"Artigo gerado: {result['title']}")
        print(f"Caminho: {result['output_path']}")
        print(f"Palavras: {result['word_count']}")

    print("\n=== Demonstração Concluída ===")


if __name__ == "__main__":
    asyncio.run(main())
