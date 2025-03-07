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
       python examples/workflow_automation/workflow_orchestration.py
"""

import asyncio
import os
import random
from typing import Any, Dict

from pepperpy.workflows.public import (
    BaseWorkflow,
    WorkflowStatus,
    WorkflowStep,
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
    await asyncio.sleep(1)  # Simular tempo de processamento

    # Gerar dados aleatórios
    items = []
    for i in range(random.randint(1, max_items)):
        items.append({"id": i, "value": random.randint(1, 100)})

    return {
        "source": source_url,
        "count": len(items),
        "items": items,
    }


async def process_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula o processamento de dados.

    Args:
        params: Parâmetros da função
            - data: Dados a serem processados
            - operation: Operação a ser realizada (sum, average, etc.)

    Returns:
        Resultado do processamento
    """
    data = params.get("data", {})
    operation = params.get("operation", "sum")

    print(f"Processando dados com operação '{operation}'")
    await asyncio.sleep(0.5)  # Simular tempo de processamento

    items = data.get("items", [])
    if not items:
        return {"result": {"total": 0, "count": 0}}

    if operation == "sum":
        total = sum(item["value"] for item in items)
        return {"result": {"total": total, "count": len(items)}}
    elif operation == "average":
        total = sum(item["value"] for item in items)
        average = total / len(items)
        return {"result": {"total": total, "average": average, "count": len(items)}}
    else:
        raise ValueError(f"Operação não suportada: {operation}")


async def save_result(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula o salvamento de resultados.

    Args:
        params: Parâmetros da função
            - data: Dados a serem salvos
            - output_path: Caminho do arquivo de saída

    Returns:
        Informações sobre o salvamento
    """
    data = params.get("data", {})
    output_path = params.get("output_path", "outputs/result.json")

    print(f"Salvando resultados em {output_path}")
    await asyncio.sleep(0.5)  # Simular tempo de processamento

    # Criar diretório se não existir
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Simular salvamento
    return {
        "path": output_path,
        "size": len(str(data)),
        "timestamp": "2023-01-01T12:00:00Z",
    }


async def notify_completion(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula o envio de notificação de conclusão.

    Args:
        params: Parâmetros da função
            - result: Resultado do processamento
            - notification_type: Tipo de notificação (email, sms, etc.)

    Returns:
        Informações sobre a notificação
    """
    result = params.get("result", {})
    notification_type = params.get("notification_type", "email")

    print(f"Enviando notificação de conclusão via {notification_type}")
    await asyncio.sleep(0.2)  # Simular tempo de processamento

    return {
        "type": notification_type,
        "status": "sent",
        "timestamp": "2023-01-01T12:30:00Z",
    }


# Implementação de um workflow simples
class SimpleWorkflow(BaseWorkflow):
    """Workflow simples de processamento de dados."""

    def __init__(self, name: str, description: str = ""):
        """Inicializar workflow.

        Args:
            name: Nome do workflow
            description: Descrição do workflow
        """
        self.name = name
        self.description = description
        self.steps = {}
        self.status = WorkflowStatus.PENDING
        self.outputs = {}
        self.error = None

    async def execute(self, inputs: Dict[str, Any] = None) -> None:
        """Executar o workflow.

        Args:
            inputs: Entradas para o workflow
        """
        if inputs is None:
            inputs = {}

        print(f"Executando workflow '{self.name}'")
        self.status = WorkflowStatus.RUNNING

        try:
            # Executar passos do workflow
            for step_name, step in self.steps.items():
                print(f"Executando passo '{step_name}'")

                # Preparar parâmetros para o passo
                step_params = {}

                # Verificar dependências
                for dep in step.dependencies:
                    if dep in self.outputs:
                        step_params[dep + "_output"] = self.outputs[dep]

                # Adicionar parâmetros específicos do passo
                if step_name == "fetch":
                    step_params.update({
                        "source_url": "https://example.com/api/data",
                        "max_items": 5,
                    })
                elif step_name == "process":
                    step_params.update({
                        "data": self.outputs.get("fetch", {}),
                        "operation": "sum",
                    })
                elif step_name == "save":
                    step_params.update({
                        "data": self.outputs.get("process", {}),
                        "output_path": "outputs/workflow_result.json",
                    })
                elif step_name == "notify":
                    step_params.update({
                        "result": self.outputs.get("save", {}),
                        "notification_type": "email",
                    })

                # Executar função do passo
                result = await step.function(step_params)
                self.outputs[step_name] = result

            self.status = WorkflowStatus.COMPLETED
            print(f"Workflow '{self.name}' concluído com sucesso")

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.error = str(e)
            print(f"Erro ao executar workflow '{self.name}': {e}")


async def run_workflow(workflow: BaseWorkflow) -> None:
    """Executa um workflow e exibe o resultado.

    Args:
        workflow: Workflow a ser executado
    """
    print(f"\n=== Executando Workflow: {workflow.name} ===")
    print(f"Descrição: {workflow.description}")

    # Executar o workflow
    await workflow.execute()

    # Exibir resultado
    print(f"\nResultado: {workflow.status}")

    if workflow.status == WorkflowStatus.COMPLETED:
        print("Saída:")
        for step_id, step_output in workflow.outputs.items():
            print(f"  {step_id}: {step_output}")
    else:
        print(f"Erro: {workflow.error}")


def create_data_processing_workflow() -> BaseWorkflow:
    """Cria um workflow de processamento de dados.

    Returns:
        Workflow de processamento de dados
    """
    workflow = SimpleWorkflow(
        name="Workflow de Processamento de Dados",
        description="Busca, processa e salva dados",
    )

    # Adicionar passos ao workflow
    workflow.steps["fetch"] = WorkflowStep(
        name="fetch", function=fetch_data, dependencies=[]
    )

    workflow.steps["process"] = WorkflowStep(
        name="process", function=process_data, dependencies=["fetch"]
    )

    workflow.steps["save"] = WorkflowStep(
        name="save", function=save_result, dependencies=["process"]
    )

    workflow.steps["notify"] = WorkflowStep(
        name="notify", function=notify_completion, dependencies=["save"]
    )

    return workflow


async def main():
    """Função principal."""
    print("=== Exemplo Avançado: Orquestração de Fluxos de Trabalho ===")
    print(
        "Este exemplo demonstra como orquestrar fluxos de trabalho complexos no PepperPy."
    )

    # Criar e executar workflow de processamento de dados
    data_workflow = create_data_processing_workflow()
    await run_workflow(data_workflow)


if __name__ == "__main__":
    asyncio.run(main())
