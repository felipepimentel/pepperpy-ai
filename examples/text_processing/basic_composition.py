#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo básico de composição no PepperPy.

Purpose:
    Demonstrar o uso básico da API de composição universal do PepperPy,
    mostrando como criar pipelines simples para processamento de dados.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/quickstart/basic_composition.py
"""

import asyncio
from typing import Any, Dict

from pepperpy.core.composition import compose


# Definir componentes simples para o exemplo
class SimpleTextSource:
    """Componente de fonte que fornece um texto simples."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - text: Texto a ser fornecido
        """
        self.text = config.get("text", "Texto padrão para processamento")

    async def fetch(self) -> str:
        """Busca o texto configurado.

        Returns:
            O texto configurado
        """
        print(f"Fonte: Fornecendo texto de {len(self.text)} caracteres")
        return self.text


class TextTransformProcessor:
    """Componente de processamento que transforma texto."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - operation: Operação a ser aplicada (upper, lower, capitalize)
        """
        self.operation = config.get("operation", "upper")

    async def transform(self, text: str) -> str:
        """Transforma o texto de acordo com a operação configurada.

        Args:
            text: Texto a ser transformado

        Returns:
            Texto transformado
        """
        print(f"Processador: Aplicando operação '{self.operation}' ao texto")

        if self.operation == "upper":
            return text.upper()
        elif self.operation == "lower":
            return text.lower()
        elif self.operation == "capitalize":
            return text.capitalize()
        else:
            return text


class ConsoleOutputComponent:
    """Componente de saída que exibe o resultado no console."""

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            config: Configuração do componente
                - prefix: Prefixo a ser adicionado à saída
        """
        self.prefix = config.get("prefix", "Resultado: ")

    async def output(self, text: str) -> str:
        """Exibe o texto no console.

        Args:
            text: Texto a ser exibido

        Returns:
            O texto exibido
        """
        result = f"{self.prefix}{text}"
        print("\nSaída:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        return result


async def demo_basic_pipeline():
    """Demonstra um pipeline básico de processamento de texto."""
    print("\n=== Pipeline Básico ===")

    # Criar e executar um pipeline simples
    result = await (
        compose("basic_pipeline")
        .source(
            SimpleTextSource({
                "text": "Este é um exemplo de pipeline de composição no PepperPy."
            })
        )
        .process(TextTransformProcessor({"operation": "upper"}))
        .output(ConsoleOutputComponent({"prefix": "Texto processado: "}))
        .execute()
    )

    print(f"\nPipeline executado com sucesso. Resultado: '{result}'")


async def demo_multiple_processors():
    """Demonstra um pipeline com múltiplos processadores."""
    print("\n=== Pipeline com Múltiplos Processadores ===")

    # Criar um pipeline com múltiplos processadores em sequência
    result = await (
        compose("multi_processor_pipeline")
        .source(SimpleTextSource({"text": "exemplo de múltiplos processadores."}))
        .process(TextTransformProcessor({"operation": "capitalize"}))
        .process(TextTransformProcessor({"operation": "upper"}))
        .output(ConsoleOutputComponent({"prefix": "Resultado final: "}))
        .execute()
    )

    print(f"\nPipeline com múltiplos processadores executado. Resultado: '{result}'")


async def main():
    """Função principal."""
    print("=== Exemplo Básico de Composição ===")
    print("Este exemplo demonstra o uso básico da API de composição do PepperPy.")

    # Demonstrar pipeline básico
    await demo_basic_pipeline()

    # Demonstrar pipeline com múltiplos processadores
    await demo_multiple_processors()

    print("\n=== Conceitos Demonstrados ===")
    print("1. Criação de componentes de fonte, processamento e saída")
    print("2. Composição de pipelines usando a API fluente")
    print("3. Execução de pipelines e obtenção de resultados")
    print("4. Encadeamento de múltiplos processadores")


if __name__ == "__main__":
    asyncio.run(main())
