#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exemplo de uso das importações simplificadas do PepperPy Framework v0.3.0+.

Este exemplo demonstra como usar as importações após a refatoração de consolidação
realizada na versão 0.3.0, que simplificou a estrutura de diretórios.
"""

import asyncio

# Importações no novo formato (após v0.3.0)
from pepperpy.config import ConfigLoader
from pepperpy.core.common import CommonUtils
from pepperpy.core.intent import IntentBuilder
from pepperpy.di import Container
from pepperpy.http.client import HTTPClient
from pepperpy.lifecycle import LifecycleManager
from pepperpy.memory import MemoryCache
from pepperpy.rag.pipeline.stages.generation import LLMGenerator
from pepperpy.rag.pipeline.stages.reranking import SemanticReranker
from pepperpy.rag.pipeline.stages.retrieval import VectorRetriever
from pepperpy.storage import FileStorage


async def main():
    """Função principal que demonstra o uso das importações simplificadas."""
    print("PepperPy Framework - Exemplo de Importações Simplificadas")
    print("=======================================================\n")

    # Configuração usando o módulo consolidado
    config = ConfigLoader.load("config.json")
    print(f"Configuração carregada: {config}")

    # Uso do container de injeção de dependência
    container = Container()
    container.register(HTTPClient)
    container.register(MemoryCache)
    container.register(FileStorage)

    # Demonstração do serviço HTTP
    http_client = container.resolve(HTTPClient)
    response = await http_client.get("https://jsonplaceholder.typicode.com/todos/1")
    print(f"Resposta HTTP: {response.json()}")

    # Demonstração de processamento de intenção
    intent = (
        IntentBuilder("greeting")
        .with_confidence(0.95)
        .with_parameter("name", "mundo")
        .build()
    )
    print(f"Intenção criada: {intent}")

    # Demonstração de RAG
    generator = LLMGenerator(model="gpt-3.5-turbo")
    retriever = VectorRetriever(collection_name="documentos")
    reranker = SemanticReranker(model="all-mpnet-base-v2")

    print("\nPipeline RAG configurado com:")
    print(f"- Retriever: {retriever.__class__.__name__}")
    print(f"- Reranker: {reranker.__class__.__name__}")
    print(f"- Generator: {generator.__class__.__name__}")

    # Demonstração do ciclo de vida
    lifecycle = LifecycleManager()
    lifecycle.register(http_client)

    await lifecycle.start_all()
    print("\nTodos os serviços iniciados.")

    # Uso do utilitário comum
    formatted_date = CommonUtils.format_date()
    print(f"\nData formatada: {formatted_date}")

    await lifecycle.stop_all()
    print("Todos os serviços parados.")


if __name__ == "__main__":
    asyncio.run(main())
