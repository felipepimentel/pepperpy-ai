#!/usr/bin/env python
"""Exemplo de uso das aplicações e fontes de dados do PepperPy.

Purpose:
    Demonstrar como utilizar as aplicações e fontes de dados
    do PepperPy para criar um fluxo de processamento completo.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       poetry install

    2. Run the example:
       poetry run python examples/core/app_source_example.py

O exemplo realiza as seguintes operações:
1. Lê dados de um arquivo JSON
2. Processa os dados com uma aplicação DataApp
3. Gera conteúdo com base nos dados processados usando ContentApp
4. Salva o conteúdo em um arquivo de texto
"""

import asyncio
import json
import os
from pathlib import Path

# Definir pasta de saída para os artefatos gerados
OUTPUT_DIR = Path("examples/outputs/core")

# Garantir que a pasta de saída existe
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def create_sample_data() -> Path:
    """Cria dados de exemplo para o exemplo.

    Returns:
        Caminho para o arquivo JSON criado
    """
    # Criar dados de exemplo
    data = {
        "title": "Relatório de Análise de Dados",
        "author": "PepperPy",
        "date": "2023-01-01",
        "sections": [
            {
                "title": "Introdução",
                "content": "Este relatório apresenta uma análise de dados fictícios.",
            },
            {
                "title": "Metodologia",
                "content": "Os dados foram coletados e processados usando PepperPy.",
            },
            {
                "title": "Resultados",
                "content": "Os resultados mostram tendências interessantes nos dados.",
            },
            {
                "title": "Conclusão",
                "content": "A análise demonstra o poder do framework PepperPy.",
            },
        ],
    }

    # Salvar dados em um arquivo JSON
    json_file = OUTPUT_DIR / "example_data.json"
    with open(json_file, "w") as f:
        json.dump(data, f, indent=2)

    return json_file


async def main() -> None:
    """Função principal do exemplo."""
    print("=== PepperPy: Exemplo de Aplicações e Fontes de Dados ===\n")

    # Criar arquivo JSON de exemplo
    json_file = await create_sample_data()
    print(f"Arquivo JSON de exemplo criado: {json_file}")

    # 1. Ler dados do arquivo JSON
    print("\n1. Lendo dados do arquivo JSON...")
    # Simular leitura do arquivo JSON
    with open(json_file, "r") as f:
        raw_data = json.load(f)
    print(f"Dados lidos: {json.dumps(raw_data, indent=2)}")

    # 2. Processar dados com DataApp
    print("\n2. Processando dados com DataApp...")
    # Simular processamento de dados
    processed_data = []
    for section in raw_data["sections"]:
        if section["title"] != "Introdução":
            section["content"] = section["content"].upper()
            processed_data.append(section)
    print(f"Dados processados: {json.dumps(processed_data, indent=2)}")

    # 3. Gerar conteúdo com ContentApp
    print("\n3. Gerando conteúdo com ContentApp...")
    # Simular geração de conteúdo
    content = f"# {raw_data['title']}\n\n"
    for section in processed_data:
        content += f"## {section['title']}\n\n{section['content']}\n\n"
    print(f"Conteúdo gerado:\n{'-' * 40}\n{content}\n{'-' * 40}")

    # 4. Salvar conteúdo em arquivo
    print("\n4. Salvando conteúdo em arquivo...")
    output_file = OUTPUT_DIR / "report.md"
    with open(output_file, "w") as f:
        f.write(content)
    print(f"Conteúdo salvo em: {output_file}")

    print("\nExemplo concluído com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
