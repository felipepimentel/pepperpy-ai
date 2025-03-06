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
import random
from datetime import datetime
from typing import Any, Dict

from pepperpy.workflows.engine import execute_workflow
from pepperpy.workflows.types import WorkflowDefinition


# Simulação de funções para o workflow
async def fetch_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Simula a busca de dados de uma fonte externa.

    Args:
        params: Parâmetros da busca
            - source: Fonte de dados
            - query: Consulta
            - timeout: Tempo limite em segundos

    Returns:
        Dados obtidos

    Raises:
        Exception: Se ocorrer um erro na busca
    """
    source = params.get("source", "default")
    query = params.get("query", "")
    timeout = params.get("timeout", 5)

    print(f"Buscando dados de '{source}' com consulta '{query}'")
    print(f"Timeout: {timeout}s")

    # Simular tempo de processamento
    await asyncio.sleep(random.uniform(0.5, 2.0))

    # Simular falha aleatória (20% de chance)
    if random.random() < 0.2 and not params.get("retry", False):
        raise Exception(f"Erro ao conectar com a fonte '{source}'")

    # Dados simulados
    return {
        "source": source,
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "results": [
            {"id": 1, "value": f"Resultado 1 para {query}", "score": 0.95},
            {"id": 2, "value": f"Resultado 2 para {query}", "score": 0.87},
            {"id": 3, "value": f"Resultado 3 para {query}", "score": 0.76},
        ],
        "metadata": {"total_results": 3, "processing_time": random.uniform(0.5, 2.0)},
    }


async def validate_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Valida os dados obtidos.

    Args:
        params: Parâmetros da validação
            - data: Dados a serem validados
            - min_score: Pontuação mínima para considerar válido

    Returns:
        Resultado da validação
    """
    data = params.get("data", {})
    min_score = params.get("min_score", 0.8)

    print(f"Validando dados com pontuação mínima de {min_score}")

    # Simular tempo de processamento
    await asyncio.sleep(random.uniform(0.2, 0.8))

    # Validar resultados
    valid_results = []
    invalid_results = []

    for result in data.get("results", []):
        if result.get("score", 0) >= min_score:
            valid_results.append(result)
        else:
            invalid_results.append(result)

    is_valid = len(valid_results) > 0

    return {
        "is_valid": is_valid,
        "valid_results": valid_results,
        "invalid_results": invalid_results,
        "validation_timestamp": datetime.now().isoformat(),
        "original_data": data,
    }


async def process_valid_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Processa dados válidos.

    Args:
        params: Parâmetros do processamento
            - data: Dados a serem processados
            - format: Formato de saída

    Returns:
        Dados processados
    """
    data = params.get("data", {})
    output_format = params.get("format", "json")

    print(f"Processando dados válidos no formato '{output_format}'")

    # Simular tempo de processamento
    await asyncio.sleep(random.uniform(0.5, 1.5))

    # Processar dados
    processed_results = []

    for result in data.get("valid_results", []):
        processed_results.append({
            "id": result.get("id"),
            "processed_value": f"Processado: {result.get('value')}",
            "original_score": result.get("score"),
            "enhanced_score": min(1.0, result.get("score", 0) * 1.1),
        })

    return {
        "format": output_format,
        "processed_results": processed_results,
        "processing_timestamp": datetime.now().isoformat(),
        "metadata": {
            "result_count": len(processed_results),
            "average_score": sum(r.get("enhanced_score", 0) for r in processed_results)
            / max(1, len(processed_results)),
        },
    }


async def handle_invalid_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Trata dados inválidos.

    Args:
        params: Parâmetros do tratamento
            - data: Dados a serem tratados
            - action: Ação a ser tomada (log, retry, fallback)

    Returns:
        Resultado do tratamento
    """
    data = params.get("data", {})
    action = params.get("action", "log")

    print(f"Tratando dados inválidos com ação '{action}'")

    # Simular tempo de processamento
    await asyncio.sleep(random.uniform(0.3, 0.7))

    if action == "log":
        return {
            "action_taken": "log",
            "message": f"Registrado {len(data.get('invalid_results', []))} resultados inválidos",
            "timestamp": datetime.now().isoformat(),
            "invalid_data": data.get("invalid_results", []),
        }

    elif action == "retry":
        return {
            "action_taken": "retry",
            "message": "Solicitando nova tentativa com parâmetros ajustados",
            "timestamp": datetime.now().isoformat(),
            "retry_params": {
                "source": data.get("original_data", {}).get("source"),
                "query": data.get("original_data", {}).get("query"),
                "timeout": 10,  # Timeout aumentado
                "retry": True,
            },
        }

    elif action == "fallback":
        return {
            "action_taken": "fallback",
            "message": "Utilizando dados de fallback",
            "timestamp": datetime.now().isoformat(),
            "fallback_data": [
                {"id": 99, "value": "Resultado de fallback 1", "score": 0.85},
                {"id": 100, "value": "Resultado de fallback 2", "score": 0.82},
            ],
        }

    else:
        return {
            "action_taken": "unknown",
            "message": f"Ação desconhecida: {action}",
            "timestamp": datetime.now().isoformat(),
        }


async def generate_report(params: Dict[str, Any]) -> Dict[str, Any]:
    """Gera um relatório com os resultados.

    Args:
        params: Parâmetros do relatório
            - processed_data: Dados processados
            - invalid_data_result: Resultado do tratamento de dados inválidos
            - format: Formato do relatório

    Returns:
        Relatório gerado
    """
    processed_data = params.get("processed_data", {})
    invalid_data_result = params.get("invalid_data_result", {})
    report_format = params.get("format", "text")

    print(f"Gerando relatório no formato '{report_format}'")

    # Simular tempo de processamento
    await asyncio.sleep(random.uniform(0.5, 1.0))

    # Dados para o relatório
    processed_results = processed_data.get("processed_results", [])
    invalid_action = invalid_data_result.get("action_taken", "none")
    invalid_message = invalid_data_result.get("message", "")

    # Gerar relatório
    if report_format == "text":
        report_content = "=== RELATÓRIO DE PROCESSAMENTO ===\n\n"
        report_content += f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        report_content += f"Total de resultados processados: {len(processed_results)}\n"
        report_content += f"Ação para dados inválidos: {invalid_action}\n"
        report_content += f"Mensagem: {invalid_message}\n\n"

        report_content += "--- RESULTADOS PROCESSADOS ---\n"
        for result in processed_results:
            report_content += f"ID: {result.get('id')}\n"
            report_content += f"Valor: {result.get('processed_value')}\n"
            report_content += f"Pontuação: {result.get('enhanced_score'):.2f}\n"
            report_content += "---\n"

    elif report_format == "json":
        report_content = {
            "timestamp": datetime.now().isoformat(),
            "processed_results_count": len(processed_results),
            "invalid_data_action": invalid_action,
            "invalid_data_message": invalid_message,
            "processed_results": processed_results,
        }

    else:
        report_content = f"Formato de relatório não suportado: {report_format}"

    return {
        "format": report_format,
        "content": report_content,
        "generated_at": datetime.now().isoformat(),
    }


# Definição de workflows
def create_data_processing_workflow(source: str, query: str) -> WorkflowDefinition:
    """Cria um workflow de processamento de dados com ramificações condicionais.

    Args:
        source: Fonte de dados
        query: Consulta

    Returns:
        Definição do workflow
    """
    return {
        "id": "data_processing_workflow",
        "name": f"Processamento de dados de {source}",
        "description": f"Workflow para buscar e processar dados de {source} com consulta '{query}'",
        "steps": [
            {
                "id": "fetch",
                "name": "Buscar Dados",
                "function": fetch_data,
                "params": {"source": source, "query": query, "timeout": 5},
                "retry": {"max_attempts": 3, "delay_seconds": 2, "backoff_factor": 1.5},
            },
            {
                "id": "validate",
                "name": "Validar Dados",
                "function": validate_data,
                "params": {"min_score": 0.8},
                "input_mapping": {"data": "$.fetch.output"},
            },
            {
                "id": "branch",
                "name": "Ramificação Condicional",
                "type": "condition",
                "condition": "$.validate.output.is_valid",
                "if_true": "process_valid",
                "if_false": "handle_invalid",
            },
            {
                "id": "process_valid",
                "name": "Processar Dados Válidos",
                "function": process_valid_data,
                "params": {"format": "json"},
                "input_mapping": {"data": "$.validate.output"},
            },
            {
                "id": "handle_invalid",
                "name": "Tratar Dados Inválidos",
                "function": handle_invalid_data,
                "params": {"action": "retry"},
                "input_mapping": {"data": "$.validate.output"},
            },
            {
                "id": "retry_decision",
                "name": "Decisão de Retentativa",
                "type": "condition",
                "condition": "$.handle_invalid.output.action_taken == 'retry'",
                "if_true": "retry_fetch",
                "if_false": "generate_report",
            },
            {
                "id": "retry_fetch",
                "name": "Retentativa de Busca",
                "function": fetch_data,
                "input_mapping": {
                    "source": "$.handle_invalid.output.retry_params.source",
                    "query": "$.handle_invalid.output.retry_params.query",
                    "timeout": "$.handle_invalid.output.retry_params.timeout",
                    "retry": "$.handle_invalid.output.retry_params.retry",
                },
            },
            {
                "id": "retry_validate",
                "name": "Validar Dados da Retentativa",
                "function": validate_data,
                "params": {
                    "min_score": 0.7  # Critério mais flexível na retentativa
                },
                "input_mapping": {"data": "$.retry_fetch.output"},
            },
            {
                "id": "retry_branch",
                "name": "Ramificação da Retentativa",
                "type": "condition",
                "condition": "$.retry_validate.output.is_valid",
                "if_true": "process_retry_valid",
                "if_false": "fallback",
            },
            {
                "id": "process_retry_valid",
                "name": "Processar Dados Válidos da Retentativa",
                "function": process_valid_data,
                "params": {"format": "json"},
                "input_mapping": {"data": "$.retry_validate.output"},
            },
            {
                "id": "fallback",
                "name": "Usar Fallback",
                "function": handle_invalid_data,
                "params": {"action": "fallback"},
                "input_mapping": {"data": "$.retry_validate.output"},
            },
            {
                "id": "generate_report",
                "name": "Gerar Relatório",
                "function": generate_report,
                "params": {"format": "text"},
                "input_mapping": {
                    "processed_data": "$.process_valid.output || $.process_retry_valid.output",
                    "invalid_data_result": "$.handle_invalid.output || $.fallback.output",
                },
            },
        ],
    }


async def demo_complex_workflow():
    """Demonstra o uso de um workflow complexo com ramificações condicionais."""
    print("\n=== Demonstração de Workflow Complexo ===")

    # Definir fontes e consultas para teste
    test_cases = [
        {"source": "api", "query": "inteligência artificial"},
        {"source": "database", "query": "aprendizado de máquina"},
        {"source": "web", "query": "processamento de linguagem natural"},
    ]

    for case in test_cases:
        source = case["source"]
        query = case["query"]

        print(f"\nExecutando workflow para fonte '{source}' e consulta '{query}'")

        # Criar e executar workflow
        workflow = create_data_processing_workflow(source, query)
        result = await execute_workflow(workflow)

        # Exibir resultado
        if result.status == "success":
            print("Workflow concluído com sucesso!")

            # Verificar qual caminho foi seguido
            if "process_valid" in result.outputs:
                print("Caminho: Dados válidos na primeira tentativa")
                print(
                    f"Resultados processados: {len(result.outputs['process_valid']['processed_results'])}"
                )

            elif "process_retry_valid" in result.outputs:
                print("Caminho: Dados válidos após retentativa")
                print(
                    f"Resultados processados: {len(result.outputs['process_retry_valid']['processed_results'])}"
                )

            elif "fallback" in result.outputs:
                print("Caminho: Fallback após falha na retentativa")
                print(f"Ação de fallback: {result.outputs['fallback']['action_taken']}")

            # Exibir informações do relatório
            if "generate_report" in result.outputs:
                report_format = result.outputs["generate_report"]["format"]
                if report_format == "text":
                    print("\nRelatório gerado:")
                    print("-" * 50)
                    print(result.outputs["generate_report"]["content"])
                    print("-" * 50)
                else:
                    print(f"\nRelatório gerado no formato {report_format}")

        else:
            print(f"Erro ao executar workflow: {result.error}")

        print("=" * 50)


async def main():
    """Função principal."""
    print("=== Exemplo de Workflow Complexo ===")
    print(
        "Este exemplo demonstra como criar workflows complexos com ramificações condicionais,"
    )
    print("tratamento de erros e retentativas usando o PepperPy.")

    await demo_complex_workflow()

    print("\n=== Recursos Demonstrados ===")
    print("1. Definição de workflows com ramificações condicionais")
    print("2. Tratamento de erros e retentativas")
    print("3. Uso de fallbacks para garantir resiliência")
    print("4. Mapeamento dinâmico de entradas entre etapas")
    print("5. Geração de relatórios baseados no caminho de execução")


if __name__ == "__main__":
    asyncio.run(main())
