#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo introdutório ao framework PepperPy.

Purpose:
    Demonstrar os conceitos básicos do framework PepperPy com um exemplo simples
    que mostra como usar as principais APIs.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/quickstart/hello_pepperpy.py
"""

import asyncio

from pepperpy.core.composition import Outputs, Processors, Sources, compose
from pepperpy.core.intent import recognize_intent


async def demo_composition():
    """Demonstra o uso da API de composição universal."""
    print("\n=== Demonstração da API de Composição ===")

    # Criar um pipeline simples para buscar e processar dados
    result = await (
        compose("hello_pipeline")
        .source(Sources.text("Olá, mundo! Este é um exemplo do PepperPy."))
        .process(Processors.transform(lambda text: text.upper()))
        .output(Outputs.console())
        .execute()
    )

    print(f"Pipeline executado com sucesso: {result}")


async def demo_intent():
    """Demonstra o uso da API de intenção."""
    print("\n=== Demonstração da API de Intenção ===")

    # Reconhecer uma intenção a partir de um texto
    text = "resumir o artigo em https://example.com/article"
    print(f"Texto do usuário: '{text}'")

    intent = await recognize_intent(text)
    print(f"Intenção reconhecida: {intent.name}")
    print(f"Tipo: {intent.type.value}")
    print(f"Confiança: {intent.confidence:.2f}")
    print(f"Entidades: {intent.entities}")

    # Processar a intenção (simulado)
    print("Processando intenção...")
    result = {
        "status": "success",
        "message": "Artigo resumido com sucesso",
        "summary": "Este é um resumo simulado do artigo.",
    }
    print(f"Resultado: {result}")


async def demo_template():
    """Demonstra o uso da API de templates."""
    print("\n=== Demonstração da API de Templates ===")

    # Configurar parâmetros para o template
    params = {
        "source_url": "https://example.com/news",
        "output_path": "outputs/news_summary.txt",
        "max_items": 3,
        "summary_length": 100,
    }

    print(f"Executando template 'news_summary' com parâmetros: {params}")

    # Executar o template (simulado)
    result = {
        "status": "success",
        "output_path": "outputs/news_summary.txt",
        "message": "Resumo de notícias gerado com sucesso",
    }

    print(f"Template executado com sucesso: {result}")


async def main():
    """Função principal que executa todas as demonstrações."""
    print("=== Hello PepperPy! ===")
    print("Este exemplo demonstra os conceitos básicos do framework PepperPy.")

    # Demonstrar a API de composição
    await demo_composition()

    # Demonstrar a API de intenção
    await demo_intent()

    # Demonstrar a API de templates
    await demo_template()

    print("\n=== Conclusão ===")
    print("Você viu os três níveis de abstração do PepperPy:")
    print("1. Composição Universal (baixo nível): Para controle granular")
    print("2. Abstração por Intenção (médio nível): Para comandos em linguagem natural")
    print("3. Templates (alto nível): Para casos de uso comuns pré-configurados")
    print("\nPara mais exemplos, explore os diretórios:")
    print("- examples/use_cases/: Exemplos de casos de uso reais")
    print("- examples/advanced/: Exemplos avançados")
    print("- examples/integration/: Exemplos de integração entre sistemas")


if __name__ == "__main__":
    asyncio.run(main())
