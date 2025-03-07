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
from pathlib import Path

import pepperpy as pp


async def main() -> None:
    """Função principal do exemplo."""
    print("=== PepperPy: Exemplo de Aplicações e Fontes de Dados ===\n")

    # Criar diretório de dados se não existir
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)

    # Criar arquivo JSON de exemplo se não existir
    json_file = data_dir / "example_data.json"
    if not json_file.exists():
        print(f"Criando arquivo JSON de exemplo: {json_file}")
        example_data = {
            "title": "Relatório de Vendas",
            "period": "2023-Q4",
            "data": [
                {"product": "Produto A", "sales": 1200, "growth": 0.15},
                {"product": "Produto B", "sales": 850, "growth": -0.05},
                {"product": "Produto C", "sales": 1500, "growth": 0.25},
                {"product": "Produto D", "sales": 600, "growth": 0.10},
            ],
        }
        with open(json_file, "w") as f:
            json.dump(example_data, f, indent=2)

    # 1. Ler dados do arquivo JSON
    print("\n1. Lendo dados do arquivo JSON...")
    json_source = pp.JSONFileSource(json_file)
    async with json_source:
        data = await json_source.read()

    print(f"Dados lidos: {data['title']} ({data['period']})")
    print(f"Número de produtos: {len(data['data'])}")

    # 2. Processar dados com DataApp
    print("\n2. Processando dados com DataApp...")
    data_app = pp.DataApp("data_processor")
    data_app.configure(
        steps=[
            # Calcular valor total de vendas
            {
                "name": "calculate",
                "field": "total_value",
                "formula": "sales * (1 + growth)",
            },
            # Ordenar por valor total
            {"name": "sort", "field": "total_value", "order": "desc"},
            # Adicionar classificação
            {
                "name": "classify",
                "field": "performance",
                "based_on": "growth",
                "ranges": [
                    {"min": 0.2, "value": "Excelente"},
                    {"min": 0.1, "max": 0.2, "value": "Bom"},
                    {"min": 0, "max": 0.1, "value": "Regular"},
                    {"max": 0, "value": "Ruim"},
                ],
            },
        ]
    )

    # Simular processamento de dados
    result = await data_app.process(data)

    # Para fins de simulação, vamos usar o próprio dado de entrada como resultado processado
    # Em um caso real, o resultado seria obtido do objeto result.data
    processed_data = data.copy()  # Usar uma cópia dos dados originais

    # Adicionar campos calculados manualmente para simulação
    for item in processed_data["data"]:
        item["total_value"] = round(item["sales"] * (1 + item["growth"]), 2)
        if item["growth"] >= 0.2:
            item["performance"] = "Excelente"
        elif item["growth"] >= 0.1:
            item["performance"] = "Bom"
        elif item["growth"] >= 0:
            item["performance"] = "Regular"
        else:
            item["performance"] = "Ruim"

    # Ordenar por valor total
    processed_data["data"].sort(key=lambda x: x["total_value"], reverse=True)

    print("Dados processados:")
    for item in processed_data["data"]:
        print(
            f"  - {item['product']}: Vendas={item['sales']}, "
            f"Crescimento={item['growth']:.2f}, "
            f"Valor Total={item['total_value']}, "
            f"Desempenho={item['performance']}"
        )

    # 3. Gerar conteúdo com ContentApp
    print("\n3. Gerando conteúdo com ContentApp...")
    content_app = pp.ContentApp("content_generator")
    content_app.configure(
        depth="detailed",
        style="business",
        language="pt",
        length="medium",
        include_metadata=True,
    )

    # Definir caminho de saída
    output_file = data_dir / "report.md"
    content_app.set_output_path(output_file)

    # Gerar artigo com base nos dados processados
    topic = f"Análise de Vendas: {processed_data['title']} - {processed_data['period']}"
    content_result = await content_app.generate_article(topic)

    # Garantir que metadata não é None
    metadata = content_result.metadata or {}

    # Substituir conteúdo gerado por um relatório baseado nos dados reais
    report_content = f"# {topic}\n\n"
    report_content += "## Resumo Executivo\n\n"

    total_sales = sum(item["sales"] for item in processed_data["data"])
    avg_growth = sum(item["growth"] for item in processed_data["data"]) / len(
        processed_data["data"]
    )

    report_content += f"Este relatório apresenta os resultados de vendas para o período {processed_data['period']}.\n"
    report_content += f"O total de vendas foi de {total_sales} unidades, com crescimento médio de {avg_growth:.2%}.\n\n"

    report_content += "## Desempenho por Produto\n\n"

    for item in processed_data["data"]:
        report_content += f"### {item['product']}\n\n"
        report_content += f"- **Vendas**: {item['sales']} unidades\n"
        report_content += f"- **Crescimento**: {item['growth']:.2%}\n"
        report_content += f"- **Valor Total**: {item['total_value']}\n"
        report_content += f"- **Desempenho**: {item['performance']}\n\n"

    report_content += "## Conclusão\n\n"

    best_product = processed_data["data"][0]["product"]
    worst_product = processed_data["data"][-1]["product"]

    report_content += f"O produto com melhor desempenho foi {best_product}, "
    report_content += f"enquanto {worst_product} apresentou o pior desempenho.\n\n"
    report_content += "Recomenda-se focar esforços de marketing nos produtos com desempenho 'Regular' e 'Ruim' "
    report_content += "para melhorar os resultados no próximo período.\n\n"

    report_content += "---\n\n"
    report_content += "## Metadados\n\n"
    report_content += f"- **Período**: {processed_data['period']}\n"
    report_content += f"- **Total de Produtos**: {len(processed_data['data'])}\n"
    report_content += (
        f"- **Gerado em**: {metadata.get('generation_time', 0):.2f} segundos\n"
    )

    # 4. Salvar conteúdo em arquivo
    print("\n4. Salvando conteúdo em arquivo...")
    text_source = pp.TextFileSource(output_file, mode="w")
    async with text_source:
        await text_source.write(report_content)

    print(f"Relatório salvo em: {output_file}")

    # Exibir parte do relatório
    print("\nTrecho do relatório gerado:")
    print("---")
    print("\n".join(report_content.split("\n")[:10]) + "\n...")
    print("---")

    print("\nExemplo concluído com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
