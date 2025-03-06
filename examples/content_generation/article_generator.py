#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gerador de artigos usando PepperPy.

Purpose:
    Demonstrar como criar um gerador de artigos que produz conteúdo
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
from typing import Any, Dict

from pepperpy.core.composition import compose


class TopicAnalyzer:
    """Componente para analisar e expandir um tópico em subtópicos."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - depth: Profundidade da análise (basic, detailed, comprehensive)
                - language: Idioma do conteúdo
        """
        self.depth = config.get("depth", "detailed")
        self.language = config.get("language", "pt")

    async def fetch(self) -> Dict[str, Any]:
        """Analisa o tópico e gera subtópicos.

        Returns:
            Estrutura do artigo com tópico principal e subtópicos
        """
        topic = "Inteligência Artificial na Educação"
        print(f"Analisando tópico: {topic}")
        print(f"Profundidade: {self.depth}, Idioma: {self.language}")

        # Simulação de análise de tópico
        if self.depth == "basic":
            subtopics = [
                "O que é IA na educação",
                "Benefícios da IA na educação",
                "Desafios da implementação",
            ]
        elif self.depth == "detailed":
            subtopics = [
                "O que é IA na educação",
                "Tecnologias de IA usadas em educação",
                "Benefícios para estudantes",
                "Benefícios para educadores",
                "Desafios éticos",
                "Desafios de implementação",
                "Estudos de caso",
            ]
        else:  # comprehensive
            subtopics = [
                "Definição de IA na educação",
                "História da IA na educação",
                "Tecnologias de IA usadas em educação",
                "Machine Learning em sistemas educacionais",
                "Processamento de linguagem natural em educação",
                "Sistemas de tutoria inteligente",
                "Personalização do aprendizado",
                "Automação de tarefas administrativas",
                "Benefícios para estudantes",
                "Benefícios para educadores",
                "Benefícios para instituições",
                "Desafios éticos",
                "Privacidade e segurança de dados",
                "Desafios de implementação",
                "Custo e acessibilidade",
                "Estudos de caso",
                "Futuro da IA na educação",
            ]

        return {
            "topic": topic,
            "subtopics": subtopics,
            "language": self.language,
            "depth": self.depth,
        }


class ContentGenerator:
    """Componente para gerar conteúdo para cada subtópico."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - style: Estilo de escrita (academic, journalistic, conversational)
                - length: Comprimento médio de cada seção (short, medium, long)
        """
        self.style = config.get("style", "journalistic")
        self.length = config.get("length", "medium")

    async def transform(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Gera conteúdo para cada subtópico.

        Args:
            structure: Estrutura do artigo com tópico e subtópicos

        Returns:
            Artigo com conteúdo gerado
        """
        topic = structure["topic"]
        subtopics = structure["subtopics"]
        language = structure["language"]

        print(f"Gerando conteúdo para {len(subtopics)} subtópicos")
        print(f"Estilo: {self.style}, Comprimento: {self.length}")

        # Determinar comprimento aproximado por seção
        if self.length == "short":
            words_per_section = 100
        elif self.length == "medium":
            words_per_section = 250
        else:  # long
            words_per_section = 500

        # Simulação de geração de conteúdo
        introduction = f"Introdução sobre {topic}. " * 5

        sections = []
        for i, subtopic in enumerate(subtopics):
            # Simular conteúdo de seção
            section_content = f"Conteúdo sobre {subtopic}. " * (words_per_section // 10)

            sections.append({
                "title": subtopic,
                "content": section_content,
                "order": i + 1,
            })

        conclusion = f"Conclusão sobre {topic} e seus impactos. " * 5

        return {
            "topic": topic,
            "introduction": introduction,
            "sections": sections,
            "conclusion": conclusion,
            "metadata": {
                "language": language,
                "style": self.style,
                "word_count": len(introduction.split())
                + sum(len(s["content"].split()) for s in sections)
                + len(conclusion.split()),
                "section_count": len(sections),
            },
        }


class ArticleFormatter:
    """Componente para formatar o artigo em diferentes formatos."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - format: Formato de saída (markdown, html, text)
                - output_path: Caminho para salvar o resultado
                - include_metadata: Se deve incluir metadados
        """
        self.format = config.get("format", "markdown")
        self.output_path = config.get("output_path", "outputs/article.md")
        self.include_metadata = config.get("include_metadata", False)

        # Criar diretório de saída se não existir
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    async def output(self, article: Dict[str, Any]) -> str:
        """Formata e salva o artigo.

        Args:
            article: Artigo com conteúdo gerado

        Returns:
            Caminho do arquivo de saída
        """
        topic = article["topic"]
        introduction = article["introduction"]
        sections = article["sections"]
        conclusion = article["conclusion"]
        metadata = article["metadata"]

        print(f"Formatando artigo no formato {self.format}")

        # Formatar artigo de acordo com o formato especificado
        if self.format == "markdown":
            content = f"# {topic}\n\n"
            content += f"{introduction}\n\n"

            for section in sections:
                content += f"## {section['title']}\n\n"
                content += f"{section['content']}\n\n"

            content += "## Conclusão\n\n"
            content += f"{conclusion}\n\n"

            if self.include_metadata:
                content += "---\n\n"
                content += "## Metadados\n\n"
                for key, value in metadata.items():
                    content += f"- **{key}**: {value}\n"

        elif self.format == "html":
            content = f"<h1>{topic}</h1>\n"
            content += f"<p>{introduction}</p>\n"

            for section in sections:
                content += f"<h2>{section['title']}</h2>\n"
                content += f"<p>{section['content']}</p>\n"

            content += "<h2>Conclusão</h2>\n"
            content += f"<p>{conclusion}</p>\n"

            if self.include_metadata:
                content += "<hr>\n"
                content += "<h2>Metadados</h2>\n"
                content += "<ul>\n"
                for key, value in metadata.items():
                    content += f"<li><strong>{key}</strong>: {value}</li>\n"
                content += "</ul>\n"

        else:  # text
            content = f"{topic.upper()}\n\n"
            content += f"{introduction}\n\n"

            for section in sections:
                content += f"{section['title'].upper()}\n\n"
                content += f"{section['content']}\n\n"

            content += "CONCLUSÃO\n\n"
            content += f"{conclusion}\n\n"

            if self.include_metadata:
                content += "----------\n\n"
                content += "METADADOS:\n\n"
                for key, value in metadata.items():
                    content += f"{key}: {value}\n"

        # Salvar conteúdo no arquivo
        with open(self.output_path, "w") as f:
            f.write(content)

        print(f"Artigo salvo em: {self.output_path}")
        return self.output_path


async def generate_article(
    depth: str = "detailed",
    language: str = "pt",
    style: str = "journalistic",
    length: str = "medium",
    output_format: str = "markdown",
    output_path: str = None,
    include_metadata: bool = False,
) -> str:
    """Gera um artigo sobre um tópico.

    Args:
        depth: Profundidade da análise (basic, detailed, comprehensive)
        language: Idioma do conteúdo
        style: Estilo de escrita (academic, journalistic, conversational)
        length: Comprimento médio de cada seção (short, medium, long)
        output_format: Formato de saída (markdown, html, text)
        output_path: Caminho para salvar o resultado
        include_metadata: Se deve incluir metadados

    Returns:
        Caminho do arquivo de artigo gerado
    """
    # Definir caminho de saída padrão se não especificado
    if output_path is None:
        extension = (
            "md"
            if output_format == "markdown"
            else "html"
            if output_format == "html"
            else "txt"
        )
        output_path = f"outputs/article.{extension}"

    # Criar pipeline de geração de artigo
    article_path = await (
        compose("article_generator")
        .source(TopicAnalyzer({"depth": depth, "language": language}))
        .process(ContentGenerator({"style": style, "length": length}))
        .output(
            ArticleFormatter({
                "format": output_format,
                "output_path": output_path,
                "include_metadata": include_metadata,
            })
        )
        .execute()
    )

    return article_path


async def main():
    """Função principal."""
    print("=== Gerador de Artigos ===")

    # Exemplo 1: Artigo básico em markdown
    print("\n--- Exemplo 1: Artigo básico em markdown ---")
    await generate_article(
        depth="basic",
        style="journalistic",
        length="short",
        output_format="markdown",
        output_path="outputs/artigo_basico.md",
    )

    # Exemplo 2: Artigo detalhado em HTML
    print("\n--- Exemplo 2: Artigo detalhado em HTML ---")
    await generate_article(
        depth="detailed",
        style="academic",
        length="medium",
        output_format="html",
        output_path="outputs/artigo_detalhado.html",
        include_metadata=True,
    )

    # Exemplo 3: Artigo abrangente em texto simples
    print("\n--- Exemplo 3: Artigo abrangente em texto simples ---")
    await generate_article(
        depth="comprehensive",
        language="en",
        style="conversational",
        length="long",
        output_format="text",
        output_path="outputs/comprehensive_article.txt",
        include_metadata=True,
    )

    print("\n=== Artigos Gerados com Sucesso ===")
    print("Os artigos foram salvos na pasta 'outputs/'")
    print("\nPara personalizar a geração, você pode:")
    print("1. Modificar os parâmetros da função generate_article()")
    print("2. Adaptar os componentes para comportamentos personalizados")
    print("3. Integrar com APIs externas para obter dados reais")


if __name__ == "__main__":
    asyncio.run(main())
