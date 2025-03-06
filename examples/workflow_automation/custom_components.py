#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo avançado de criação de componentes personalizados no PepperPy.

Purpose:
    Demonstrar como criar componentes personalizados para o sistema de composição,
    implementando interfaces específicas e estendendo a funcionalidade do framework.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/workflow_automation/custom_components.py
"""

import asyncio
import json
import os
from typing import Any, Dict, TypeVar

from pepperpy.core.composition import compose
from pepperpy.core.composition.types import (
    OutputComponent,
    ProcessorComponent,
    SourceComponent,
)

# Definir tipos genéricos para os componentes
T = TypeVar("T")
U = TypeVar("U")


class JSONFileSource(SourceComponent[Dict[str, Any]]):
    """Componente de fonte personalizado para carregar dados de arquivos JSON."""

    def __init__(self, file_path: str):
        """Inicializa o componente.

        Args:
            file_path: Caminho para o arquivo JSON
        """
        self.file_path = file_path

    async def read(self) -> Dict[str, Any]:
        """Lê dados da fonte.

        Returns:
            Dados lidos da fonte.
        """
        return await self.fetch()

    async def fetch(self) -> Dict[str, Any]:
        """Carrega dados de um arquivo JSON.

        Returns:
            Dados carregados do arquivo JSON
        """
        print(f"Carregando dados do arquivo JSON: {self.file_path}")

        # Simulação de carregamento (em um caso real, carregaria do arquivo)
        data = {
            "title": "Exemplo de Dados",
            "items": [
                {"id": 1, "name": "Item 1", "value": 10},
                {"id": 2, "name": "Item 2", "value": 20},
                {"id": 3, "name": "Item 3", "value": 30},
            ],
            "metadata": {"source": self.file_path, "timestamp": "2023-01-01T12:00:00Z"},
        }

        return data


class FilterProcessor(ProcessorComponent[Dict[str, Any], Dict[str, Any]]):
    """Componente de processamento personalizado para filtrar dados."""

    def __init__(self, filter_criteria: Dict[str, Any]):
        """Inicializa o componente.

        Args:
            filter_criteria: Critérios de filtragem
        """
        self.filter_criteria = filter_criteria

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa os dados de entrada.

        Args:
            data: Dados a serem processados.

        Returns:
            Dados processados.
        """
        return await self.transform(data)

    async def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filtra os dados de acordo com os critérios especificados.

        Args:
            data: Dados a serem filtrados

        Returns:
            Dados filtrados
        """
        print(f"Aplicando filtro: {self.filter_criteria}")

        # Extrair itens dos dados
        items = data.get("items", [])

        # Aplicar filtro
        filtered_items = []
        for item in items:
            match = True
            for key, value in self.filter_criteria.items():
                if key in item and item[key] != value:
                    match = False
                    break

            if match:
                filtered_items.append(item)

        # Criar nova estrutura de dados com itens filtrados
        filtered_data = data.copy()
        filtered_data["items"] = filtered_items
        filtered_data["metadata"]["filtered"] = True
        filtered_data["metadata"]["filter_criteria"] = self.filter_criteria
        filtered_data["metadata"]["original_count"] = len(items)
        filtered_data["metadata"]["filtered_count"] = len(filtered_items)

        return filtered_data


class TransformProcessor(ProcessorComponent[Dict[str, Any], Dict[str, Any]]):
    """Componente de processamento personalizado para transformar dados."""

    def __init__(self, transform_function: str):
        """Inicializa o componente.

        Args:
            transform_function: Nome da função de transformação a ser aplicada
        """
        self.transform_function = transform_function

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa os dados de entrada.

        Args:
            data: Dados a serem processados.

        Returns:
            Dados processados.
        """
        return await self.transform(data)

    async def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma os dados de acordo com a função especificada.

        Args:
            data: Dados a serem transformados

        Returns:
            Dados transformados
        """
        print(f"Aplicando transformação: {self.transform_function}")

        # Extrair itens dos dados
        items = data.get("items", [])

        # Aplicar transformação
        if self.transform_function == "double_value":
            for item in items:
                if "value" in item:
                    item["value"] = item["value"] * 2

        elif self.transform_function == "uppercase_name":
            for item in items:
                if "name" in item:
                    item["name"] = item["name"].upper()

        elif self.transform_function == "add_prefix":
            for item in items:
                if "name" in item:
                    item["name"] = f"PREFIX_{item['name']}"

        # Criar nova estrutura de dados com itens transformados
        transformed_data = data.copy()
        transformed_data["items"] = items
        transformed_data["metadata"]["transformed"] = True
        transformed_data["metadata"]["transform_function"] = self.transform_function

        return transformed_data


class JSONFileOutput(OutputComponent[Dict[str, Any]]):
    """Componente de saída personalizado para salvar dados em arquivos JSON."""

    def __init__(self, output_path: str, pretty: bool = True):
        """Inicializa o componente.

        Args:
            output_path: Caminho para o arquivo de saída
            pretty: Se deve formatar o JSON de forma legível
        """
        self.output_path = output_path
        self.pretty = pretty

        # Criar diretório de saída se não existir
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    async def write(self, data: Dict[str, Any]) -> str:
        """Escreve os dados no destino.

        Args:
            data: Dados a serem escritos.

        Returns:
            Resultado da operação.
        """
        return await self.output(data)

    async def output(self, data: Dict[str, Any]) -> str:
        """Salva os dados em um arquivo JSON.

        Args:
            data: Dados a serem salvos

        Returns:
            Caminho do arquivo de saída
        """
        print(f"Salvando dados em: {self.output_path}")

        # Adicionar metadados de saída
        data["metadata"]["output_path"] = self.output_path
        data["metadata"]["output_timestamp"] = "2023-01-01T12:30:00Z"

        # Simular salvamento (em um caso real, salvaria no arquivo)
        print(
            f"Dados a serem salvos: {json.dumps(data, indent=2 if self.pretty else None)}"
        )

        return self.output_path


class ConsoleOutput(OutputComponent[Dict[str, Any]]):
    """Componente de saída personalizado para exibir dados no console."""

    def __init__(self, format: str = "json"):
        """Inicializa o componente.

        Args:
            format: Formato de saída (json, table, summary)
        """
        self.format = format

    async def write(self, data: Dict[str, Any]) -> str:
        """Escreve os dados no destino.

        Args:
            data: Dados a serem escritos.

        Returns:
            Resultado da operação.
        """
        return await self.output(data)

    async def output(self, data: Dict[str, Any]) -> str:
        """Exibe os dados no console.

        Args:
            data: Dados a serem exibidos

        Returns:
            Descrição da saída
        """
        print(f"\n=== Saída no formato {self.format} ===")

        if self.format == "json":
            print(json.dumps(data, indent=2))

        elif self.format == "table":
            # Exibir itens em formato de tabela
            items = data.get("items", [])
            if items:
                # Cabeçalho
                headers = items[0].keys()
                header_str = " | ".join(str(h) for h in headers)
                separator = "-" * len(header_str)
                print(header_str)
                print(separator)

                # Linhas
                for item in items:
                    row = " | ".join(str(item.get(h, "")) for h in headers)
                    print(row)

        elif self.format == "summary":
            # Exibir resumo dos dados
            items = data.get("items", [])
            print(f"Título: {data.get('title', 'N/A')}")
            print(f"Total de itens: {len(items)}")

            if "metadata" in data:
                print("\nMetadados:")
                for key, value in data["metadata"].items():
                    print(f"  {key}: {value}")

        return f"Dados exibidos no console no formato {self.format}"


async def demo_custom_pipeline():
    """Demonstra o uso de componentes personalizados em um pipeline."""
    print("\n=== Pipeline com Componentes Personalizados ===")

    # Criar e executar o pipeline
    result = await (
        compose("custom_pipeline")
        .source(JSONFileSource("data/example.json"))
        .process(FilterProcessor({"id": 2}))
        .process(TransformProcessor("double_value"))
        .output(JSONFileOutput("output/processed_data.json"))
        .execute()
    )

    print(f"Pipeline executado com sucesso. Resultado: {result}")


async def demo_multiple_outputs():
    """Demonstra o uso de múltiplos componentes de saída."""
    print("\n=== Pipeline com Múltiplas Saídas ===")

    # Criar fonte e processadores
    source = JSONFileSource("data/example.json")
    filter_processor = FilterProcessor({"value": 20})
    transform_processor = TransformProcessor("uppercase_name")

    # Criar saídas
    json_output = JSONFileOutput("output/filtered_data.json")
    console_output = ConsoleOutput(format="table")

    # Criar e executar o pipeline com a primeira saída
    result1 = await (
        compose("output_pipeline_1")
        .source(source)
        .process(filter_processor)
        .output(json_output)
        .execute()
    )

    print(f"Primeira saída: {result1}")

    # Criar e executar o pipeline com a segunda saída
    result2 = await (
        compose("output_pipeline_2")
        .source(source)
        .process(transform_processor)
        .output(console_output)
        .execute()
    )

    print(f"Segunda saída: {result2}")


async def demo_component_chaining():
    """Demonstra o encadeamento de múltiplos processadores."""
    print("\n=== Encadeamento de Processadores ===")

    # Criar e executar o pipeline com múltiplos processadores
    result = await (
        compose("chained_pipeline")
        .source(JSONFileSource("data/example.json"))
        .process(FilterProcessor({"value": 30}))
        .process(TransformProcessor("uppercase_name"))
        .process(TransformProcessor("add_prefix"))
        .output(ConsoleOutput(format="summary"))
        .execute()
    )

    print(f"Pipeline encadeado executado com sucesso. Resultado: {result}")


async def main():
    """Função principal."""
    print("=== Exemplo Avançado: Componentes Personalizados ===")
    print(
        "Este exemplo demonstra como criar e usar componentes personalizados no PepperPy."
    )

    # Demonstrar pipeline com componentes personalizados
    await demo_custom_pipeline()

    # Demonstrar pipeline com múltiplas saídas
    await demo_multiple_outputs()

    # Demonstrar encadeamento de processadores
    await demo_component_chaining()

    print("\n=== Conceitos Demonstrados ===")
    print(
        "1. Criação de componentes personalizados implementando interfaces específicas"
    )
    print("2. Uso de tipos genéricos para garantir segurança de tipos")
    print("3. Encadeamento de múltiplos processadores em um pipeline")
    print("4. Uso de múltiplos componentes de saída")
    print("5. Personalização do comportamento dos componentes")


if __name__ == "__main__":
    asyncio.run(main())
