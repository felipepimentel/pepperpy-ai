#!/usr/bin/env python3
"""Exemplo de análise de repositórios com PepperPy.

Este exemplo demonstra o uso dos Enhancers (Potencializadores) implementados
no PepperPy para análise de repositórios.
"""

import asyncio
import os

# Importação do pepperpy
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from pepperpy.pepperpy import (
    Enhancer,
    GitRepository,
    enhancer,
)

# Criar diretório de saída necessário
OUTPUT_DIR = Path(__file__).parent / "output" / "repos"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Demonstração de enhancers customizados
async def demonstrate_custom_enhancer():
    """Demonstrar como criar e usar enhancers customizados."""
    print("\nEnhancers Customizados")
    print("=" * 50)

    # Definir uma classe de enhancer customizada
    class DomainSpecificEnhancer(Enhancer):
        """Enhancer customizado para um domínio específico."""

        def __init__(self, domain: str, expertise_level: str = "expert"):
            """
            Inicializa o enhancer de domínio específico.

            Args:
                domain: Domínio de conhecimento
                expertise_level: Nível de expertise
            """
            super().__init__(
                "domain_specific", domain=domain, expertise_level=expertise_level
            )

        def enhance_prompt(self, prompt: str) -> str:
            """
            Melhora o prompt com conhecimento de domínio específico.

            Args:
                prompt: Prompt original

            Returns:
                Prompt melhorado
            """
            domain = self.config.get("domain", "geral")
            expertise = self.config.get("expertise_level", "expert")

            domain_prompt = (
                f"\n\nAnalize esta questão com conhecimento especializado em {domain}, "
                f"em nível de {expertise}. Considere padrões, práticas e desafios "
                f"específicos deste domínio."
            )

            return prompt + domain_prompt

    # Usar o enhancer customizado
    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    repo = GitRepository(url=repo_url)
    await repo.ensure_cloned()
    agent = await repo.get_agent()

    # Criar enhancer customizado
    custom_enhancer = DomainSpecificEnhancer(
        domain="interface homem-máquina", expertise_level="especialista"
    )

    # Aplicar enhancer
    context = custom_enhancer.apply_to_context({})
    prompt = custom_enhancer.enhance_prompt(
        "Como melhorar a usabilidade desta aplicação?"
    )

    # Executar análise
    print("\nAnálise com enhancer customizado:")
    result = await agent.ask(prompt, repo_url=repo.url, **context)
    result = custom_enhancer.enhance_result(result)

    print(f"\nResultado com enhancer customizado: {result[:200]}...")

    # Usar enhancers built-in
    print("\nTeste de enhancers built-in:")

    # Deep Context Enhancer
    deep_context = enhancer.deep_context(depth=4)
    context = deep_context.apply_to_context({})
    prompt = deep_context.enhance_prompt("Como esta biblioteca está estruturada?")

    deep_result = await agent.ask(prompt, repo_url=repo.url, **context)
    deep_result = deep_context.enhance_result(deep_result)

    print(f"\nResultado com Deep Context Enhancer: {deep_result[:200]}...")

    # Security Enhancer
    sec_enhancer = enhancer.security(compliance=["OWASP Top 10"])
    context = sec_enhancer.apply_to_context({})
    prompt = sec_enhancer.enhance_prompt(
        "Quais são os possíveis problemas de segurança neste código?"
    )

    security_result = await agent.ask(prompt, repo_url=repo.url, **context)
    security_result = sec_enhancer.enhance_result(security_result)

    print(f"\nResultado com Security Enhancer: {security_result[:200]}...")

    # Performance Enhancer
    perf_enhancer = enhancer.performance(hotspots=True, algorithms=True)
    context = perf_enhancer.apply_to_context({})
    prompt = perf_enhancer.enhance_prompt(
        "Identifique possíveis gargalos de desempenho nesta aplicação."
    )

    perf_result = await agent.ask(prompt, repo_url=repo.url, **context)
    perf_result = perf_enhancer.enhance_result(perf_result)

    print(f"\nResultado com Performance Enhancer: {perf_result[:200]}...")

    # Combinação de enhancers
    print("\nCombinando múltiplos enhancers:")
    enhancers_list = [
        enhancer.deep_context(depth=3),
        enhancer.best_practices(framework="Python"),
        enhancer.performance(hotspots=True),
    ]

    context = {}
    prompt = "Como melhorar a arquitetura deste projeto para maior escalabilidade?"

    # Aplicar cada enhancer ao contexto e prompt
    for e in enhancers_list:
        context = e.apply_to_context(context)
        prompt = e.enhance_prompt(prompt)

    combined_result = await agent.ask(prompt, repo_url=repo.url, **context)

    # Aplicar enhancers ao resultado
    for e in enhancers_list:
        combined_result = e.enhance_result(combined_result)

    print(f"\nResultado com enhancers combinados: {combined_result[:200]}...")

    return "Demonstração concluída"


async def main():
    """Função principal."""
    print("\n===== ENHANCERS DO PEPPERPY =====")
    print("Demonstração das capacidades de potencialização de análises")

    try:
        await demonstrate_custom_enhancer()
        print("\nDemonstração concluída com sucesso!")
    except Exception as e:
        print(f"Erro na demonstração: {e}")

    print("\nExemplo de enhancers concluído!")


if __name__ == "__main__":
    asyncio.run(main())
