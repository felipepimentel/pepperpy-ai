#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo avançado de orquestração de fluxos de trabalho no PepperPy.

Purpose:
    Demonstrar como orquestrar fluxos de trabalho complexos usando o sistema
    de workflows do PepperPy, incluindo execução condicional, tratamento de erros
    e composição de workflows.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/advanced/workflow_orchestration.py
"""

import asyncio
import os
import random
from typing import Any, Dict

from pepperpy.workflows.engine import execute_workflow
from pepperpy.workflows.types import (
    WorkflowDefinition,
    WorkflowStatus,
)


# Simulação de funções de processamento
async def fetch_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula a busca de dados de uma fonte externa.

    Args:
        params: Parâmetros da função
            - source_url: URL da fonte de dados
            - max_items: Número máximo de itens

    Returns:
        Dados obtidos
    """
    source_url = params.get("source_url", "https://example.com/api")
    max_items = params.get("max_items", 5)

    print(f"Buscando dados de {source_url} (máximo de {max_items} itens)")

    # Simulação de busca de dados
    items = []
    for i in range(1, max_items + 1):
        items.append({"id": i, "title": f"Item {i}", "value": random.randint(10, 100)})

    return {"source": source_url, "items": items, "count": len(items)}


async def process_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula o processamento de dados.

    Args:
        params: Parâmetros da função
            - data: Dados a serem processados
            - operation: Operação a ser aplicada

    Returns:
        Dados processados
    """
    data = params.get("data", {})
    operation = params.get("operation", "sum")

    items = data.get("items", [])
    print(f"Processando {len(items)} itens com operação '{operation}'")

    # Aplicar operação
    if operation == "sum":
        total = sum(item.get("value", 0) for item in items)
        result = {"total": total}

    elif operation == "average":
        values = [item.get("value", 0) for item in items]
        avg = sum(values) / len(values) if values else 0
        result = {"average": avg}

    elif operation == "filter":
        threshold = params.get("threshold", 50)
        filtered = [item for item in items if item.get("value", 0) >= threshold]
        result = {"filtered_items": filtered, "count": len(filtered)}

    else:
        result = {"error": f"Operação desconhecida: {operation}"}

    return {"operation": operation, "input_count": len(items), "result": result}


async def save_result(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula o salvamento de resultados.

    Args:
        params: Parâmetros da função
            - data: Dados a serem salvos
            - output_path: Caminho para salvar os dados

    Returns:
        Informações sobre o salvamento
    """
    data = params.get("data", {})
    output_path = params.get("output_path", "output/result.json")

    print(f"Salvando resultados em {output_path}")

    # Simular salvamento
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    return {"output_path": output_path, "size": len(str(data)), "success": True}


async def notify_completion(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula o envio de notificação de conclusão.

    Args:
        params: Parâmetros da função
            - result: Resultado do processamento
            - notification_type: Tipo de notificação

    Returns:
        Informações sobre a notificação
    """
    result = params.get("result", {})
    notification_type = params.get("notification_type", "email")

    print(f"Enviando notificação via {notification_type}")

    return {
        "notification_type": notification_type,
        "sent_at": "2023-01-01T13:00:00Z",
        "success": True,
    }


# Definição de workflows
def create_data_processing_workflow() -> WorkflowDefinition:
    """Cria um workflow de processamento de dados.

    Returns:
        Definição do workflow
    """
    return {
        "id": "data_processing_workflow",
        "name": "Workflow de Processamento de Dados",
        "description": "Busca, processa e salva dados",
        "steps": [
            {
                "id": "fetch",
                "name": "Buscar Dados",
                "function": fetch_data,
                "params": {
                    "source_url": "https://example.com/api/data",
                    "max_items": 10,
                },
            },
            {
                "id": "process",
                "name": "Processar Dados",
                "function": process_data,
                "params": {"operation": "sum"},
                "input_mapping": {"data": "$.fetch.output"},
            },
            {
                "id": "save",
                "name": "Salvar Resultados",
                "function": save_result,
                "params": {"output_path": "output/processed_data.json"},
                "input_mapping": {"data": "$.process.output"},
            },
            {
                "id": "notify",
                "name": "Notificar Conclusão",
                "function": notify_completion,
                "params": {"notification_type": "email"},
                "input_mapping": {"result": "$.process.output"},
            },
        ],
    }


def create_conditional_workflow() -> WorkflowDefinition:
    """Cria um workflow com execução condicional.

    Returns:
        Definição do workflow
    """
    return {
        "id": "conditional_workflow",
        "name": "Workflow com Execução Condicional",
        "description": "Executa etapas com base em condições",
        "steps": [
            {
                "id": "fetch",
                "name": "Buscar Dados",
                "function": fetch_data,
                "params": {
                    "source_url": "https://example.com/api/data",
                    "max_items": 5,
                },
            },
            {
                "id": "check_count",
                "name": "Verificar Quantidade",
                "function": lambda params: {
                    "has_enough_data": params.get("count", 0) >= 3
                },
                "input_mapping": {"count": "$.fetch.output.count"},
            },
            {
                "id": "process_sum",
                "name": "Calcular Soma",
                "function": process_data,
                "params": {"operation": "sum"},
                "input_mapping": {"data": "$.fetch.output"},
                "condition": "$.check_count.output.has_enough_data == true",
            },
            {
                "id": "process_average",
                "name": "Calcular Média",
                "function": process_data,
                "params": {"operation": "average"},
                "input_mapping": {"data": "$.fetch.output"},
                "condition": "$.check_count.output.has_enough_data == true",
            },
            {
                "id": "notify_insufficient",
                "name": "Notificar Dados Insuficientes",
                "function": notify_completion,
                "params": {"notification_type": "alert"},
                "condition": "$.check_count.output.has_enough_data == false",
            },
            {
                "id": "save",
                "name": "Salvar Resultados",
                "function": save_result,
                "params": {"output_path": "output/conditional_result.json"},
                "input_mapping": {
                    "data": {
                        "sum": "$.process_sum.output.result.total",
                        "average": "$.process_average.output.result.average",
                        "count": "$.fetch.output.count",
                    }
                },
                "condition": "$.check_count.output.has_enough_data == true",
            },
        ],
    }


def create_error_handling_workflow() -> WorkflowDefinition:
    """Cria um workflow com tratamento de erros.

    Returns:
        Definição do workflow
    """
    return {
        "id": "error_handling_workflow",
        "name": "Workflow com Tratamento de Erros",
        "description": "Demonstra como lidar com erros em workflows",
        "steps": [
            {
                "id": "fetch",
                "name": "Buscar Dados",
                "function": fetch_data,
                "params": {
                    "source_url": "https://example.com/api/data",
                    "max_items": 5,
                },
                "retry": {"max_attempts": 3, "delay_seconds": 1},
            },
            {
                "id": "process",
                "name": "Processar Dados",
                "function": process_data,
                "params": {
                    "operation": "invalid_operation"  # Operação inválida para simular erro
                },
                "input_mapping": {"data": "$.fetch.output"},
                "error_handler": {
                    "function": lambda error, context: {
                        "error_message": str(error),
                        "fallback_result": {"total": 0},
                    }
                },
            },
            {
                "id": "save",
                "name": "Salvar Resultados",
                "function": save_result,
                "params": {"output_path": "output/error_handling_result.json"},
                "input_mapping": {"data": "$.process.output"},
            },
            {
                "id": "notify_error",
                "name": "Notificar Erro",
                "function": notify_completion,
                "params": {"notification_type": "error_alert"},
                "input_mapping": {"result": "$.process.error"},
                "condition": "$.process.status == 'error'",
            },
        ],
    }


def create_nested_workflow() -> WorkflowDefinition:
    """Cria um workflow que utiliza outros workflows.

    Returns:
        Definição do workflow
    """
    return {
        "id": "nested_workflow",
        "name": "Workflow Aninhado",
        "description": "Demonstra como compor workflows",
        "steps": [
            {
                "id": "data_processing",
                "name": "Processamento de Dados",
                "workflow": create_data_processing_workflow(),
                "params": {
                    "source_url": "https://example.com/api/nested/data",
                    "max_items": 8,
                },
            },
            {
                "id": "conditional_processing",
                "name": "Processamento Condicional",
                "workflow": create_conditional_workflow(),
                "condition": "$.data_processing.status == 'success'",
            },
            {
                "id": "final_notification",
                "name": "Notificação Final",
                "function": notify_completion,
                "params": {"notification_type": "summary"},
                "input_mapping": {
                    "result": {
                        "data_processing": "$.data_processing.output",
                        "conditional": "$.conditional_processing.output",
                    }
                },
            },
        ],
    }


async def run_workflow(workflow_def: WorkflowDefinition) -> None:
    """Executa um workflow e exibe o resultado.

    Args:
        workflow_def: Definição do workflow
    """
    print(f"\n=== Executando Workflow: {workflow_def['name']} ===")
    print(f"Descrição: {workflow_def['description']}")

    # Executar o workflow
    result = await execute_workflow(workflow_def)

    # Exibir resultado
    print(f"\nResultado: {result.status}")

    if result.status == WorkflowStatus.SUCCESS:
        print("Saída:")
        for step_id, step_output in result.outputs.items():
            print(f"  {step_id}: {step_output}")
    else:
        print(f"Erro: {result.error}")


async def main():
    """Função principal."""
    print("=== Exemplo Avançado: Orquestração de Fluxos de Trabalho ===")
    print(
        "Este exemplo demonstra como orquestrar fluxos de trabalho complexos no PepperPy."
    )

    # Executar workflow de processamento de dados
    await run_workflow(create_data_processing_workflow())

    # Executar workflow condicional
    await run_workflow(create_conditional_workflow())

    # Executar workflow com tratamento de erros
    await run_workflow(create_error_handling_workflow())

    # Executar workflow aninhado
    await run_workflow(create_nested_workflow())

    print("\n=== Conceitos Demonstrados ===")
    print("1. Definição e execução de workflows")
    print("2. Mapeamento de entradas entre etapas")
    print("3. Execução condicional de etapas")
    print("4. Tratamento de erros e recuperação")
    print("5. Composição de workflows (workflows aninhados)")


if __name__ == "__main__":
    asyncio.run(main())
