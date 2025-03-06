#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de workflow complexo com condicionais e tratamento de erros.

Purpose:
    Demonstrar como criar workflows complexos com ramificações condicionais,
    tratamento de erros e retentativas, utilizando o framework PepperPy.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/workflow_automation/complex_workflow.py
"""

import asyncio
import logging
import random
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Definição de tipos para o workflow
class StepStatus(Enum):
    """Status de execução de um passo do workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep:
    """Representa um passo em um workflow."""

    def __init__(
        self,
        name: str,
        function: Callable[[Dict[str, Any]], Any],
        next_steps: Optional[List[Union[str, Dict[str, Any]]]] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        retry_count: int = 0,
        retry_delay: float = 1.0,
    ):
        """Inicializa um passo do workflow.

        Args:
            name: Nome do passo
            function: Função a ser executada
            next_steps: Próximos passos a serem executados
            condition: Condição para executar este passo
            retry_count: Número de tentativas em caso de falha
            retry_delay: Tempo de espera entre tentativas
        """
        self.name = name
        self.function = function
        self.next_steps = next_steps or []
        self.condition = condition
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa o passo do workflow.

        Args:
            context: Contexto do workflow

        Returns:
            Contexto atualizado
        """
        if self.condition and not self.condition(context):
            logger.info(f"Passo '{self.name}' pulado (condição não atendida)")
            self.status = StepStatus.SKIPPED
            return context

        self.status = StepStatus.RUNNING
        logger.info(f"Executando passo '{self.name}'")

        attempts = 0
        max_attempts = self.retry_count + 1

        while attempts < max_attempts:
            try:
                attempts += 1
                result = await self.function(context)
                self.result = result
                self.status = StepStatus.COMPLETED
                logger.info(f"Passo '{self.name}' concluído com sucesso")

                # Atualizar contexto com o resultado
                if isinstance(result, dict):
                    context.update(result)
                else:
                    context[self.name + "_result"] = result

                return context

            except Exception as e:
                logger.error(f"Erro no passo '{self.name}': {str(e)}")
                self.error = str(e)

                if attempts < max_attempts:
                    retry_time = self.retry_delay * attempts
                    logger.info(
                        f"Tentando novamente em {retry_time:.1f} segundos (tentativa {attempts}/{self.retry_count})"
                    )
                    await asyncio.sleep(retry_time)
                else:
                    self.status = StepStatus.FAILED
                    raise RuntimeError(
                        f"Passo '{self.name}' falhou após {attempts} tentativas: {str(e)}"
                    )

        return context


class Workflow:
    """Representa um workflow completo."""

    def __init__(self, name: str, steps: Dict[str, WorkflowStep], start_step: str):
        """Inicializa um workflow.

        Args:
            name: Nome do workflow
            steps: Dicionário de passos do workflow
            start_step: Nome do passo inicial
        """
        self.name = name
        self.steps = steps
        self.start_step = start_step
        self.initial_context: Dict[str, Any] = {}

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executa o workflow.

        Args:
            context: Contexto inicial do workflow

        Returns:
            Contexto final do workflow
        """
        context = context or {}
        logger.info(f"Iniciando workflow '{self.name}'")

        # Adicionar informações ao contexto
        context["workflow_name"] = self.name
        context["start_time"] = datetime.now().isoformat()

        try:
            # Executar o workflow a partir do passo inicial
            await self._execute_step(self.start_step, context)

            # Adicionar informações de conclusão
            context["end_time"] = datetime.now().isoformat()
            context["status"] = "completed"

            logger.info(f"Workflow '{self.name}' concluído com sucesso")
            return context

        except Exception as e:
            # Adicionar informações de erro
            context["end_time"] = datetime.now().isoformat()
            context["status"] = "failed"
            context["error"] = str(e)

            logger.error(f"Workflow '{self.name}' falhou: {str(e)}")
            raise

    async def _execute_step(self, step_name: str, context: Dict[str, Any]) -> None:
        """Executa um passo do workflow e seus próximos passos.

        Args:
            step_name: Nome do passo a ser executado
            context: Contexto do workflow
        """
        if step_name not in self.steps:
            raise ValueError(f"Passo '{step_name}' não encontrado no workflow")

        step = self.steps[step_name]

        # Executar o passo atual
        context = await step.execute(context)

        # Se o passo foi pulado ou falhou, não executar os próximos
        if step.status in [StepStatus.SKIPPED, StepStatus.FAILED]:
            return

        # Executar os próximos passos
        for next_step in step.next_steps:
            if isinstance(next_step, str):
                # Próximo passo simples
                await self._execute_step(next_step, context)
            elif isinstance(next_step, dict):
                # Próximo passo condicional
                condition = next_step.get("condition")
                target = next_step.get("target")

                if condition and target:
                    # Avaliar a condição
                    condition_func = eval(f"lambda context: {condition}")
                    if condition_func(context):
                        await self._execute_step(target, context)


# Simulação de funções para o workflow
async def fetch_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula a obtenção de dados de uma fonte externa.

    Args:
        params: Parâmetros da operação

    Returns:
        Dados obtidos

    Raises:
        RuntimeError: Se ocorrer um erro na obtenção dos dados
    """
    source = params.get("source", "default")
    query = params.get("query", "")

    logger.info(f"Obtendo dados da fonte '{source}' com query '{query}'")

    # Simular latência de rede
    await asyncio.sleep(random.uniform(0.5, 1.5))

    # Simular falha aleatória (20% de chance)
    if random.random() < 0.2:
        raise RuntimeError(f"Erro ao conectar com a fonte '{source}'")

    # Gerar dados simulados
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = {
        "source": source,
        "query": query,
        "timestamp": current_time,
        "items": [
            {"id": 1, "name": "Item 1", "value": random.randint(10, 100)},
            {"id": 2, "name": "Item 2", "value": random.randint(10, 100)},
            {"id": 3, "name": "Item 3", "value": random.randint(10, 100)},
        ],
        "metadata": {
            "total_items": 3,
            "query_time": random.uniform(0.1, 0.5),
        },
    }

    return {"data": data, "fetch_status": "success"}


async def validate_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Valida os dados obtidos.

    Args:
        params: Parâmetros da operação

    Returns:
        Resultado da validação
    """
    data = params.get("data", {})

    logger.info(f"Validando dados da fonte '{data.get('source')}'")

    # Simular processamento
    await asyncio.sleep(random.uniform(0.2, 0.8))

    # Verificar se os dados são válidos
    is_valid = True
    validation_errors = []

    # Verificar se há itens
    if not data.get("items"):
        is_valid = False
        validation_errors.append("Nenhum item encontrado")

    # Verificar valores dos itens
    for item in data.get("items", []):
        if item.get("value", 0) < 20:
            is_valid = False
            validation_errors.append(
                f"Item {item.get('id')} tem valor muito baixo: {item.get('value')}"
            )

    return {
        "validation_result": {
            "is_valid": is_valid,
            "errors": validation_errors,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    }


async def process_valid_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Processa dados válidos.

    Args:
        params: Parâmetros da operação

    Returns:
        Resultado do processamento
    """
    data = params.get("data", {})

    logger.info(f"Processando dados válidos da fonte '{data.get('source')}'")

    # Simular processamento
    await asyncio.sleep(random.uniform(0.5, 1.5))

    # Processar os itens
    processed_items = []
    total_value = 0

    for item in data.get("items", []):
        # Aplicar transformação
        processed_item = item.copy()
        processed_item["processed_value"] = item.get("value", 0) * 1.5
        processed_item["status"] = "processed"

        processed_items.append(processed_item)
        total_value += processed_item["processed_value"]

    return {
        "processing_result": {
            "processed_items": processed_items,
            "total_value": total_value,
            "average_value": total_value / len(processed_items)
            if processed_items
            else 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    }


async def handle_invalid_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Trata dados inválidos.

    Args:
        params: Parâmetros da operação

    Returns:
        Resultado do tratamento
    """
    data = params.get("data", {})
    validation_result = params.get("validation_result", {})

    logger.info(f"Tratando dados inválidos da fonte '{data.get('source')}'")
    logger.info(f"Erros de validação: {validation_result.get('errors')}")

    # Simular processamento
    await asyncio.sleep(random.uniform(0.3, 1.0))

    # Tentar corrigir os dados
    corrected_items = []
    correction_log = []

    for item in data.get("items", []):
        corrected_item = item.copy()

        # Corrigir valores muito baixos
        if item.get("value", 0) < 20:
            original_value = item.get("value", 0)
            corrected_item["value"] = 20
            corrected_item["corrected"] = True

            correction_log.append(
                f"Item {item.get('id')}: valor corrigido de {original_value} para 20"
            )

        corrected_items.append(corrected_item)

    # Verificar se a correção foi bem-sucedida
    all_corrected = all(item.get("value", 0) >= 20 for item in corrected_items)

    return {
        "correction_result": {
            "corrected_items": corrected_items,
            "correction_log": correction_log,
            "all_corrected": all_corrected,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "data": {
            **data,
            "items": corrected_items,
        },  # Atualizar os dados com os itens corrigidos
    }


async def generate_report(params: Dict[str, Any]) -> Dict[str, Any]:
    """Gera um relatório com base nos dados processados.

    Args:
        params: Parâmetros da operação

    Returns:
        Relatório gerado
    """
    data = params.get("data", {})
    processing_result = params.get("processing_result", {})
    correction_result = params.get("correction_result", {})

    logger.info(f"Gerando relatório para dados da fonte '{data.get('source')}'")

    # Simular processamento
    await asyncio.sleep(random.uniform(0.5, 1.0))

    # Determinar quais dados usar
    items = []
    if processing_result.get("processed_items"):
        items = processing_result.get("processed_items")
        report_type = "processed"
    elif correction_result.get("corrected_items"):
        items = correction_result.get("corrected_items")
        report_type = "corrected"
    else:
        items = data.get("items", [])
        report_type = "raw"

    # Gerar relatório
    report = {
        "title": f"Relatório de Dados - {data.get('source')}",
        "query": data.get("query"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "report_type": report_type,
        "summary": {
            "total_items": len(items),
            "total_value": sum(item.get("value", 0) for item in items),
            "average_value": sum(item.get("value", 0) for item in items) / len(items)
            if items
            else 0,
        },
        "items": items,
    }

    # Adicionar informações específicas do tipo de relatório
    if report_type == "processed":
        report["summary"]["total_processed_value"] = processing_result.get(
            "total_value", 0
        )
        report["summary"]["average_processed_value"] = processing_result.get(
            "average_value", 0
        )
    elif report_type == "corrected":
        report["summary"]["correction_log"] = correction_result.get(
            "correction_log", []
        )
        report["summary"]["all_corrected"] = correction_result.get(
            "all_corrected", False
        )

    return {"report": report}


def create_data_processing_workflow(source: str, query: str) -> Workflow:
    """Cria um workflow de processamento de dados.

    Args:
        source: Fonte dos dados
        query: Consulta para obtenção dos dados

    Returns:
        Workflow configurado
    """
    # Definir os passos do workflow
    steps = {
        "fetch_data": WorkflowStep(
            name="fetch_data",
            function=fetch_data,
            next_steps=["validate_data"],
            retry_count=3,
            retry_delay=1.0,
        ),
        "validate_data": WorkflowStep(
            name="validate_data",
            function=validate_data,
            next_steps=[
                {
                    "condition": "context['validation_result']['is_valid']",
                    "target": "process_valid_data",
                },
                {
                    "condition": "not context['validation_result']['is_valid']",
                    "target": "handle_invalid_data",
                },
            ],
        ),
        "process_valid_data": WorkflowStep(
            name="process_valid_data",
            function=process_valid_data,
            next_steps=["generate_report"],
            condition=lambda context: context.get("validation_result", {}).get(
                "is_valid", False
            ),
        ),
        "handle_invalid_data": WorkflowStep(
            name="handle_invalid_data",
            function=handle_invalid_data,
            next_steps=["generate_report"],
            condition=lambda context: not context.get("validation_result", {}).get(
                "is_valid", False
            ),
        ),
        "generate_report": WorkflowStep(
            name="generate_report",
            function=generate_report,
            next_steps=[],
        ),
    }

    # Criar o workflow
    workflow = Workflow(
        name="data_processing_workflow",
        steps=steps,
        start_step="fetch_data",
    )

    # Configurar o contexto inicial
    workflow.initial_context = {
        "source": source,
        "query": query,
    }

    return workflow


async def demo_complex_workflow():
    """Demonstra a execução de um workflow complexo."""
    logger.info("=== Demonstração de Workflow Complexo ===")

    # Criar e executar o workflow
    workflow = create_data_processing_workflow(
        source="api.example.com/data",
        query="type=product&category=electronics",
    )

    try:
        # Executar o workflow
        result = await workflow.execute(workflow.initial_context)

        # Exibir o relatório gerado
        report = result.get("report", {})

        logger.info(f"Relatório gerado: {report.get('title')}")
        logger.info(f"Tipo de relatório: {report.get('report_type')}")
        logger.info(f"Total de itens: {report.get('summary', {}).get('total_items')}")
        logger.info(
            f"Valor médio: {report.get('summary', {}).get('average_value'):.2f}"
        )

        # Exibir itens do relatório
        logger.info("Itens do relatório:")
        for item in report.get("items", [])[
            :3
        ]:  # Limitar a 3 itens para não poluir o log
            logger.info(
                f"  - Item {item.get('id')}: {item.get('name')} (valor: {item.get('value')})"
            )

        return result

    except Exception as e:
        logger.error(f"Erro na execução do workflow: {str(e)}")
        raise


async def main():
    """Função principal."""
    logger.info("Iniciando exemplo de workflow complexo")

    # Executar a demonstração
    await demo_complex_workflow()

    logger.info("Exemplo concluído")


if __name__ == "__main__":
    asyncio.run(main())
