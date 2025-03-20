#!/usr/bin/env python3
"""Script para testar o framework de pipeline do PepperPy.

Este script demonstra o uso das principais funcionalidades do framework de pipeline,
incluindo criação de pipelines, adição de estágios, e execução de pipelines.
"""

import logging
import sys
from typing import Any, List, cast

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("pipeline_test")

# Importar módulos do pipeline
from pepperpy.core.pipeline.base import (
    Pipeline,
    PipelineContext,
    create_pipeline,
    execute_pipeline,
)
from pepperpy.core.pipeline.stages import (
    BranchingStage,
    ConditionalStage,
    FunctionStage,
)


def test_function_stage():
    """Testa o FunctionStage."""
    logger.info("Testando FunctionStage...")

    # Criar um estágio de função simples
    def upper_case(data: str, context: PipelineContext) -> str:
        return data.upper()

    stage = FunctionStage(name="upper_case", func=upper_case)

    # Executar o estágio
    context = PipelineContext()
    result = stage("hello world", context)

    # Verificar resultado
    assert result == "HELLO WORLD"
    logger.info("✓ FunctionStage funcionou corretamente")


def test_conditional_stage():
    """Testa o ConditionalStage."""
    logger.info("Testando ConditionalStage...")

    # Criar estágios para o condicional
    true_stage = FunctionStage(name="uppercase", func=lambda x, _: cast(str, x).upper())
    false_stage = FunctionStage(
        name="prefix", func=lambda x, _: f"prefix_{cast(str, x)}"
    )

    # Criar função de condição
    def is_long(data: Any, context: PipelineContext) -> bool:
        data_str = cast(str, data)
        return len(data_str) > 5

    # Criar estágio condicional
    stage = ConditionalStage(
        name="length_check",
        condition=is_long,
        if_true=true_stage,
        if_false=false_stage,
    )

    # Testar com string curta
    context = PipelineContext()
    short_result = stage("hi", context)
    assert short_result == "prefix_hi"

    # Testar com string longa
    long_result = stage("hello world", context)
    assert long_result == "HELLO WORLD"

    logger.info("✓ ConditionalStage funcionou corretamente")


def test_branching_stage():
    """Testa o BranchingStage."""
    logger.info("Testando BranchingStage...")

    # Criar estágios para os ramos
    uppercase_stage = FunctionStage(
        name="uppercase", func=lambda x, _: cast(str, x).upper()
    )
    length_stage = FunctionStage(name="length", func=lambda x, _: len(cast(str, x)))
    reverse_stage = FunctionStage(name="reverse", func=lambda x, _: cast(str, x)[::-1])

    # Criar estágio de ramificação
    stage = BranchingStage(
        name="text_analysis",
        branches={
            "uppercase": uppercase_stage,
            "length": length_stage,
            "reverse": reverse_stage,
        },
    )

    # Executar estágio
    context = PipelineContext()
    result = stage("hello world", context)

    # Verificar resultados
    assert result["uppercase"] == "HELLO WORLD"
    assert result["length"] == 11
    assert result["reverse"] == "dlrow olleh"

    logger.info("✓ BranchingStage funcionou corretamente")


def test_pipeline():
    """Testa a criação e execução de um pipeline completo."""
    logger.info("Testando Pipeline...")

    # Criar estágios para o pipeline
    clean_stage = FunctionStage(
        name="clean",
        func=lambda x, _: cast(str, x).strip().lower(),
    )

    tokenize_stage = FunctionStage(
        name="tokenize",
        func=lambda x, _: cast(str, x).split(),
    )

    count_stage = FunctionStage(
        name="count",
        func=lambda x, _: len(cast(List[str], x)),
    )

    # Criar pipeline
    pipeline = Pipeline(
        name="text_processor",
        stages=[clean_stage, tokenize_stage, count_stage],
    )

    # Executar pipeline
    context = PipelineContext()
    result = pipeline.execute("  Hello World!  ", context)

    # Verificar resultado
    assert result == 2  # "hello" e "world!"

    logger.info("✓ Pipeline funcionou corretamente")


def test_pipeline_registry():
    """Testa o registro e execução de pipelines a partir do registro."""
    logger.info("Testando PipelineRegistry...")

    # Criar um pipeline simples
    stage = FunctionStage(
        name="square",
        func=lambda x, _: cast(int, x) ** 2,
    )

    # Registrar o pipeline
    create_pipeline(name="square_pipeline", stages=[stage])

    # Executar o pipeline a partir do registro
    result = execute_pipeline("square_pipeline", 5)

    # Verificar resultado
    assert result == 25

    logger.info("✓ PipelineRegistry funcionou corretamente")


def run_all_tests():
    """Executa todos os testes."""
    logger.info("Iniciando testes do framework de pipeline...")

    test_function_stage()
    test_conditional_stage()
    test_branching_stage()
    test_pipeline()
    test_pipeline_registry()

    logger.info("✓ Todos os testes passaram com sucesso!")


if __name__ == "__main__":
    run_all_tests()
