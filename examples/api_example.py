#!/usr/bin/env python
"""
Exemplo de uso da API unificada do PepperPy.

Este exemplo demonstra como usar a nova API simplificada do PepperPy
para realizar tarefas comuns de forma concisa e direta.
"""

import asyncio
import os
import sys

# Adiciona o diretório raiz ao sys.path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pepperpy import PepperPy, analyze, ask, create, init_framework, process


async def simple_example() -> None:
    """Demonstra o uso das funções simplificadas da API."""
    print("Inicializando framework...")
    await init_framework()

    print("\n--- Exemplo de pergunta e resposta ---")
    response = await ask("Explique de forma simples o que é inteligência artificial")
    print(f"Resposta: {response}\n")

    print("--- Exemplo de processamento de texto ---")
    text = """
    Python é uma linguagem de programação de alto nível, interpretada, de script, 
    imperativa, orientada a objetos, funcional, de tipagem dinâmica e forte. 
    Foi lançada por Guido van Rossum em 1991.
    """
    summary = await process(text, "Resuma este texto em 3 pontos principais")
    print(f"Resumo: {summary}\n")

    print("--- Exemplo de criação de conteúdo ---")
    article = await create("Um artigo curto sobre energias renováveis", format="text")
    print(f"Artigo: {article[:200]}...\n")

    try:
        print("--- Exemplo de análise de dados ---")
        data = [
            {"nome": "João", "idade": 32, "profissão": "Engenheiro"},
            {"nome": "Maria", "idade": 28, "profissão": "Médica"},
            {"nome": "Pedro", "idade": 45, "profissão": "Professor"},
            {"nome": "Ana", "idade": 29, "profissão": "Advogada"},
        ]
        insights = await analyze(
            data, "Calcule a média de idade e identifique a profissão mais comum"
        )
        print(f"Análise: {insights}\n")
    except Exception as e:
        print(f"Erro na análise: {e}")


async def advanced_example() -> None:
    """Demonstra o uso avançado da API com instância personalizada."""

    # Configura uma instância personalizada do PepperPy
    print("\n--- Exemplo avançado com configuração personalizada ---")
    pp = PepperPy()

    # Use seu próprio provedor de LLM
    # Obtenha a chave da API a partir de variáveis de ambiente para segurança
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Aviso: OPENAI_API_KEY não encontrada nas variáveis de ambiente")
        api_key = "sua-chave-aqui"  # Para exemplo (não faça isso em produção)

    # Configure o provedor de LLM
    pp.with_llm("openai", api_key=api_key, model="gpt-3.5-turbo")

    # Use contexto assíncrono para gerenciamento automático de recursos
    async with pp:
        # Use o método de alto nível
        result = await pp.ask_query("Como escrever código limpo em Python?")
        print(f"Resposta direta: {result[:150]}...\n")

        # Use o builder pattern para mais controle
        print("Usando builder pattern:")
        markdown = (
            await pp.text.with_prompt("5 dicas para escrever código limpo")
            .with_system_prompt("Você é um expert em Python")
            .as_markdown()
            .generate()
        )
        print(f"Markdown: {markdown[:150]}...\n")

        # Gere conteúdo estruturado com o content builder
        article = (
            await pp.content.blog_post("Boas práticas de programação")
            .informative()
            .in_language("pt")
            .with_max_length(500)
            .generate()
        )
        print(f"Título: {article['title']}")
        print(f"Conteúdo: {article['content'][:150]}...\n")


async def main() -> None:
    """Função principal para executar os exemplos."""
    print("=== EXEMPLOS DA API UNIFICADA DO PEPPERPY ===")

    # Exemplo básico
    await simple_example()

    # Exemplo avançado
    try:
        await advanced_example()
    except Exception as e:
        print(f"Erro no exemplo avançado: {e}")

    print("\n=== FIM DOS EXEMPLOS ===")


if __name__ == "__main__":
    asyncio.run(main())
