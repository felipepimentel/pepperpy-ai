#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Serviço de resumo de documentos usando PepperPy.

Purpose:
    Demonstrar como criar um serviço de resumo de documentos usando o framework
    PepperPy, que carrega documentos de diferentes fontes, os resume e salva
    o resultado em diferentes formatos.

Requirements:
    - Python 3.9+
    - PepperPy library
    - Documentos de exemplo (incluídos ou URLs)

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Set environment variables (optional):
       export SUMMARY_MAX_LENGTH=200

    3. Run the example:
       python examples/use_cases/document_summarizer.py
"""

import asyncio
import os
from typing import Any, Dict

from pepperpy.core.composition import compose


class DocumentSource:
    """Componente de fonte para carregar documentos."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - source_type: Tipo de fonte (file, url, text)
                - path: Caminho do arquivo ou URL
                - content: Conteúdo do texto (se source_type for text)
        """
        self.source_type = config.get("source_type", "text")
        self.path = config.get("path", "")
        self.content = config.get("content", "")

    async def fetch(self) -> Dict[str, Any]:
        """Carrega o documento da fonte especificada.

        Returns:
            Documento carregado com metadados
        """
        print(f"Carregando documento de fonte do tipo '{self.source_type}'")

        # Simulação de carregamento de documento
        if self.source_type == "file":
            print(f"Carregando arquivo: {self.path}")
            content = f"Conteúdo simulado do arquivo {self.path}. " * 10
            metadata = {"source": "file", "path": self.path, "size": len(content)}

        elif self.source_type == "url":
            print(f"Carregando URL: {self.path}")
            content = f"Conteúdo simulado da URL {self.path}. " * 10
            metadata = {"source": "url", "url": self.path, "size": len(content)}

        else:  # text
            print("Usando texto fornecido diretamente")
            content = self.content or "Conteúdo de texto padrão para resumo. " * 10
            metadata = {"source": "text", "size": len(content)}

        return {"content": content, "metadata": metadata}


class SummarizerProcessor:
    """Componente de processamento para resumir documentos."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - max_length: Tamanho máximo do resumo
                - method: Método de resumo (extractive, abstractive)
        """
        self.max_length = config.get("max_length", 150)
        self.method = config.get("method", "extractive")

    async def transform(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Resume o documento.

        Args:
            document: Documento a ser resumido

        Returns:
            Documento com resumo adicionado
        """
        content = document["content"]
        metadata = document["metadata"]

        print(f"Resumindo documento de {len(content)} caracteres")
        print(f"Método: {self.method}, Tamanho máximo: {self.max_length} caracteres")

        # Simulação de resumo
        if self.method == "extractive":
            summary = content[: self.max_length] + "..."
        else:  # abstractive
            summary = (
                f"Este é um resumo abstrato do documento original. "
                f"O documento foi resumido para aproximadamente {self.max_length} caracteres."
            )

        # Atualizar documento com o resumo
        document["summary"] = summary
        document["metadata"]["summary_method"] = self.method
        document["metadata"]["original_length"] = len(content)
        document["metadata"]["summary_length"] = len(summary)

        return document


class OutputFormatter:
    """Componente de saída para formatar e salvar resumos."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - format: Formato de saída (text, markdown, html, json)
                - output_path: Caminho para salvar o resultado
                - include_metadata: Se deve incluir metadados na saída
        """
        self.format = config.get("format", "text")
        self.output_path = config.get("output_path", "output/summary.txt")
        self.include_metadata = config.get("include_metadata", False)

        # Criar diretório de saída se não existir
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    async def output(self, document: Dict[str, Any]) -> str:
        """Formata e salva o resumo.

        Args:
            document: Documento com resumo

        Returns:
            Caminho do arquivo de saída
        """
        summary = document["summary"]
        metadata = document["metadata"]

        print(f"Formatando resumo no formato '{self.format}'")

        # Formatar saída de acordo com o formato especificado
        if self.format == "markdown":
            output = f"# Resumo do Documento\n\n{summary}\n"
            if self.include_metadata:
                output += "\n## Metadados\n\n"
                for key, value in metadata.items():
                    output += f"- **{key}**: {value}\n"

        elif self.format == "html":
            output = f"<h1>Resumo do Documento</h1>\n<p>{summary}</p>\n"
            if self.include_metadata:
                output += "<h2>Metadados</h2>\n<ul>\n"
                for key, value in metadata.items():
                    output += f"<li><strong>{key}</strong>: {value}</li>\n"
                output += "</ul>\n"

        elif self.format == "json":
            import json

            data = {
                "summary": summary,
                "metadata": metadata if self.include_metadata else {},
            }
            output = json.dumps(data, indent=2)

        else:  # text
            output = f"RESUMO DO DOCUMENTO\n\n{summary}\n"
            if self.include_metadata:
                output += "\nMETADADOS:\n\n"
                for key, value in metadata.items():
                    output += f"{key}: {value}\n"

        # Salvar saída no arquivo
        with open(self.output_path, "w") as f:
            f.write(output)

        print(f"Resumo salvo em: {self.output_path}")
        return self.output_path


async def summarize_document(
    source_type: str = "text",
    path: str = "",
    content: str = "",
    max_length: int = None,
    method: str = "extractive",
    output_format: str = "text",
    output_path: str = None,
    include_metadata: bool = False,
) -> str:
    """Resume um documento.

    Args:
        source_type: Tipo de fonte (file, url, text)
        path: Caminho do arquivo ou URL
        content: Conteúdo do texto (se source_type for text)
        max_length: Tamanho máximo do resumo
        method: Método de resumo (extractive, abstractive)
        output_format: Formato de saída (text, markdown, html, json)
        output_path: Caminho para salvar o resultado
        include_metadata: Se deve incluir metadados na saída

    Returns:
        Caminho do arquivo de resumo gerado
    """
    # Usar valores padrão ou do ambiente para parâmetros não especificados
    max_length = max_length or int(os.environ.get("SUMMARY_MAX_LENGTH", "150"))
    output_path = output_path or os.environ.get(
        "SUMMARY_OUTPUT_PATH",
        f"output/summary.{output_format if output_format != 'text' else 'txt'}",
    )

    # Criar pipeline de resumo
    summary_path = await (
        compose("document_summarizer")
        .source(
            DocumentSource({
                "source_type": source_type,
                "path": path,
                "content": content,
            })
        )
        .process(SummarizerProcessor({"max_length": max_length, "method": method}))
        .output(
            OutputFormatter({
                "format": output_format,
                "output_path": output_path,
                "include_metadata": include_metadata,
            })
        )
        .execute()
    )

    return summary_path


async def main():
    """Função principal."""
    print("=== Serviço de Resumo de Documentos ===")

    # Exemplo 1: Resumir texto fornecido diretamente
    print("\n--- Exemplo 1: Resumir texto ---")
    text_content = "Este é um exemplo de texto para ser resumido. " * 20
    await summarize_document(
        source_type="text",
        content=text_content,
        max_length=100,
        method="extractive",
        output_format="text",
        output_path="output/resumo_texto.txt",
    )

    # Exemplo 2: Resumir documento de URL simulada
    print("\n--- Exemplo 2: Resumir documento de URL ---")
    await summarize_document(
        source_type="url",
        path="https://example.com/document.pdf",
        max_length=200,
        method="abstractive",
        output_format="markdown",
        output_path="output/resumo_url.md",
        include_metadata=True,
    )

    # Exemplo 3: Resumir arquivo simulado com saída em JSON
    print("\n--- Exemplo 3: Resumir arquivo com saída em JSON ---")
    await summarize_document(
        source_type="file",
        path="documentos/exemplo.docx",
        max_length=150,
        method="extractive",
        output_format="json",
        output_path="output/resumo_arquivo.json",
        include_metadata=True,
    )

    print("\n=== Resumos Gerados com Sucesso ===")
    print("Os resumos foram salvos na pasta 'output/'")
    print("\nPara personalizar o resumo, você pode:")
    print("1. Definir variáveis de ambiente")
    print("2. Passar parâmetros diretamente para a função summarize_document()")
    print("3. Modificar os componentes do pipeline para comportamentos personalizados")


if __name__ == "__main__":
    asyncio.run(main())
