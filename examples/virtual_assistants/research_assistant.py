#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Assistente de pesquisa usando PepperPy.

Purpose:
    Demonstrar como criar um assistente de pesquisa que pode buscar informações,
    analisar documentos e gerar relatórios, utilizando o framework PepperPy
    para orquestrar o fluxo de trabalho.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/virtual_assistants/research_assistant.py
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict

from pepperpy.core.intent import register_intent_handler
from pepperpy.workflows.engine import execute_workflow
from pepperpy.workflows.types import WorkflowDefinition


# Simulação de funções de pesquisa
async def search_documents(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula a busca de documentos relacionados a um tópico.

    Args:
        params: Parâmetros da busca
            - query: Consulta de busca
            - max_results: Número máximo de resultados
            - sources: Fontes a serem consultadas

    Returns:
        Resultados da busca
    """
    query = params.get("query", "")
    max_results = params.get("max_results", 5)
    sources = params.get("sources", ["web", "academic"])

    print(f"Buscando documentos para: '{query}'")
    print(f"Fontes: {', '.join(sources)}")
    print(f"Máximo de resultados: {max_results}")

    # Simulação de resultados de busca
    results = []
    for i in range(1, max_results + 1):
        results.append({
            "id": f"doc-{i}",
            "title": f"Documento {i} sobre {query}",
            "source": sources[i % len(sources)],
            "url": f"https://example.com/doc{i}",
            "snippet": f"Este é um trecho do documento {i} que contém informações sobre {query}...",
            "relevance": 0.9 - (i * 0.1),
        })

    return {
        "query": query,
        "results": results,
        "total_found": max_results,
        "sources": sources,
    }


async def analyze_documents(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula a análise de documentos.

    Args:
        params: Parâmetros da análise
            - documents: Lista de documentos a serem analisados
            - analysis_type: Tipo de análise (summary, key_points, comparison)

    Returns:
        Resultados da análise
    """
    documents = params.get("documents", [])
    analysis_type = params.get("analysis_type", "summary")

    print(f"Analisando {len(documents)} documentos")
    print(f"Tipo de análise: {analysis_type}")

    # Simulação de análise
    if analysis_type == "summary":
        analysis = {
            "summary": f"Este é um resumo dos {len(documents)} documentos analisados. "
            * 3,
            "document_count": len(documents),
        }

    elif analysis_type == "key_points":
        key_points = []
        for i in range(1, 6):
            key_points.append(
                f"Ponto chave {i}: Informação importante encontrada nos documentos."
            )

        analysis = {"key_points": key_points, "document_count": len(documents)}

    elif analysis_type == "comparison":
        similarities = "Os documentos compartilham temas comuns e apresentam perspectivas complementares."
        differences = "Os documentos diferem em metodologia e profundidade de análise."

        analysis = {
            "similarities": similarities,
            "differences": differences,
            "document_count": len(documents),
        }

    else:
        analysis = {"error": f"Tipo de análise desconhecido: {analysis_type}"}

    return {
        "analysis_type": analysis_type,
        "analysis": analysis,
        "document_count": len(documents),
    }


async def generate_report(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula a geração de um relatório de pesquisa.

    Args:
        params: Parâmetros do relatório
            - topic: Tópico da pesquisa
            - search_results: Resultados da busca
            - analysis: Análise dos documentos
            - format: Formato do relatório (markdown, html, text)
            - output_path: Caminho para salvar o relatório

    Returns:
        Informações sobre o relatório gerado
    """
    topic = params.get("topic", "")
    search_results = params.get("search_results", {})
    analysis = params.get("analysis", {})
    report_format = params.get("format", "markdown")
    output_path = params.get(
        "output_path", f"outputs/report_{datetime.now().strftime('%Y%m%d')}.md"
    )

    print(f"Gerando relatório sobre: '{topic}'")
    print(f"Formato: {report_format}")
    print(f"Caminho de saída: {output_path}")

    # Criar diretório de saída se não existir
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Simulação de geração de relatório
    if report_format == "markdown":
        content = f"# Relatório de Pesquisa: {topic}\n\n"
        content += f"## Resumo\n\n{analysis.get('analysis', {}).get('summary', 'Sem resumo disponível.')}\n\n"

        content += "## Documentos Analisados\n\n"
        for doc in search_results.get("results", []):
            content += f"- [{doc['title']}]({doc['url']}): {doc['snippet']}\n"

        if "key_points" in analysis.get("analysis", {}):
            content += "\n## Pontos-Chave\n\n"
            for point in analysis["analysis"]["key_points"]:
                content += f"- {point}\n"

        content += f"\n## Metodologia\n\nEsta pesquisa foi realizada utilizando {len(search_results.get('sources', []))} fontes diferentes, "
        content += f"analisando um total de {search_results.get('total_found', 0)} documentos.\n\n"

        content += f"*Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}*"

    elif report_format == "html":
        content = f"<h1>Relatório de Pesquisa: {topic}</h1>\n"
        content += f"<h2>Resumo</h2>\n<p>{analysis.get('analysis', {}).get('summary', 'Sem resumo disponível.')}</p>\n"

        content += "<h2>Documentos Analisados</h2>\n<ul>\n"
        for doc in search_results.get("results", []):
            content += f"<li><a href='{doc['url']}'>{doc['title']}</a>: {doc['snippet']}</li>\n"
        content += "</ul>\n"

        if "key_points" in analysis.get("analysis", {}):
            content += "<h2>Pontos-Chave</h2>\n<ul>\n"
            for point in analysis["analysis"]["key_points"]:
                content += f"<li>{point}</li>\n"
            content += "</ul>\n"

        content += f"<h2>Metodologia</h2>\n<p>Esta pesquisa foi realizada utilizando {len(search_results.get('sources', []))} fontes diferentes, "
        content += f"analisando um total de {search_results.get('total_found', 0)} documentos.</p>\n"

        content += f"<p><em>Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</em></p>"

    else:  # text
        content = f"RELATÓRIO DE PESQUISA: {topic}\n\n"
        content += f"RESUMO\n\n{analysis.get('analysis', {}).get('summary', 'Sem resumo disponível.')}\n\n"

        content += "DOCUMENTOS ANALISADOS\n\n"
        for doc in search_results.get("results", []):
            content += f"- {doc['title']} ({doc['url']}): {doc['snippet']}\n"

        if "key_points" in analysis.get("analysis", {}):
            content += "\nPONTOS-CHAVE\n\n"
            for point in analysis["analysis"]["key_points"]:
                content += f"- {point}\n"

        content += f"\nMETODOLOGIA\n\nEsta pesquisa foi realizada utilizando {len(search_results.get('sources', []))} fontes diferentes, "
        content += f"analisando um total de {search_results.get('total_found', 0)} documentos.\n\n"

        content += f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    # Salvar relatório
    with open(output_path, "w") as f:
        f.write(content)

    return {
        "topic": topic,
        "output_path": output_path,
        "format": report_format,
        "document_count": search_results.get("total_found", 0),
        "generated_at": datetime.now().isoformat(),
    }


# Definição de workflows
def create_research_workflow(
    topic: str, output_format: str = "markdown"
) -> WorkflowDefinition:
    """Cria um workflow de pesquisa.

    Args:
        topic: Tópico da pesquisa
        output_format: Formato do relatório

    Returns:
        Definição do workflow
    """
    return {
        "id": "research_workflow",
        "name": f"Pesquisa sobre {topic}",
        "description": f"Workflow para pesquisar sobre {topic} e gerar um relatório",
        "steps": [
            {
                "id": "search",
                "name": "Buscar Documentos",
                "function": search_documents,
                "params": {
                    "query": topic,
                    "max_results": 10,
                    "sources": ["web", "academic", "news"],
                },
            },
            {
                "id": "analyze",
                "name": "Analisar Documentos",
                "function": analyze_documents,
                "params": {"analysis_type": "key_points"},
                "input_mapping": {"documents": "$.search.output.results"},
            },
            {
                "id": "report",
                "name": "Gerar Relatório",
                "function": generate_report,
                "params": {
                    "topic": topic,
                    "format": output_format,
                    "output_path": f"outputs/report_{topic.replace(' ', '_').lower()}.{output_format if output_format != 'markdown' else 'md'}",
                },
                "input_mapping": {
                    "search_results": "$.search.output",
                    "analysis": "$.analyze.output",
                },
            },
        ],
    }


# Manipuladores de intenção
async def handle_research_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de realizar uma pesquisa.

    Args:
        intent_data: Dados da intenção
            - topic: Tópico da pesquisa
            - format: Formato do relatório

    Returns:
        Resultado da pesquisa
    """
    topic = intent_data.get("topic", "Inteligência Artificial")
    output_format = intent_data.get("format", "markdown")

    print(f"Processando intenção de pesquisa sobre '{topic}'")

    # Criar e executar workflow de pesquisa
    workflow = create_research_workflow(topic, output_format)
    result = await execute_workflow(workflow)

    if result.status == "success":
        return {
            "status": "success",
            "message": f"Pesquisa sobre '{topic}' concluída com sucesso",
            "report_path": result.outputs.get("report", {}).get("output_path", ""),
            "document_count": result.outputs.get("search", {}).get("total_found", 0),
        }
    else:
        return {
            "status": "error",
            "message": f"Erro ao realizar pesquisa: {result.error}",
            "error": str(result.error),
        }


async def setup():
    """Configuração inicial do assistente."""
    # Registrar manipuladores de intenção
    register_intent_handler("research", handle_research_intent)
    print("Assistente de pesquisa configurado")


async def demo_research_assistant():
    """Demonstra o uso do assistente de pesquisa."""
    print("\n=== Demonstração do Assistente de Pesquisa ===")

    # Configurar o assistente
    await setup()

    # Simular comandos do usuário
    topics = [
        "Inteligência Artificial na Educação",
        "Mudanças Climáticas",
        "Energia Renovável",
    ]

    formats = ["markdown", "html", "text"]

    for i, topic in enumerate(topics):
        output_format = formats[i % len(formats)]

        print(f"\nComando: 'Pesquisar sobre {topic} em formato {output_format}'")

        # Simular reconhecimento de intenção
        intent = {
            "intent": "research",
            "confidence": 0.95,
            "parameters": {"topic": topic, "format": output_format},
        }

        # Processar intenção
        result = await handle_research_intent(intent["parameters"])

        # Exibir resultado
        print(f"Status: {result['status']}")
        print(f"Mensagem: {result['message']}")

        if result["status"] == "success":
            print(f"Relatório gerado: {result['report_path']}")
            print(f"Documentos analisados: {result['document_count']}")

        print("-" * 50)


async def main():
    """Função principal."""
    print("=== Assistente de Pesquisa ===")
    print(
        "Este exemplo demonstra como criar um assistente de pesquisa usando o PepperPy."
    )

    await demo_research_assistant()

    print("\n=== Recursos Demonstrados ===")
    print("1. Definição e execução de workflows de pesquisa")
    print("2. Processamento de intenções do usuário")
    print("3. Geração de relatórios em diferentes formatos")
    print("4. Integração entre sistemas de intenção e workflows")


if __name__ == "__main__":
    asyncio.run(main())
