#!/usr/bin/env python3
"""Exemplo de análise de repositórios com PepperPy.

Este exemplo demonstra como usar a API declarativa e fluida do PepperPy
para analisar repositórios GitHub e responder perguntas sobre eles,
com foco especial nos Enhancers (Potencializadores) de análise.
"""

import asyncio
import os

# Importação direta de pepperpy.py
# Nota: Em um ambiente real, você importaria diretamente de pepperpy
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from pepperpy.pepperpy import (
    AnalysisType,
    Enhancer,
    GitRepository,
    enhancer,
    event_handler,
    on_analysis_complete,
)

# Criar diretório de saída necessário
OUTPUT_DIR = Path(__file__).parent / "output" / "repos"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Registrar handlers para eventos
@event_handler("analysis.complete")
async def analysis_complete_handler(event):
    """Handler para evento de análise concluída."""
    if event.event_type == "analysis.complete":
        print(f"\n🔍 Análise concluída para: {event.data.get('target')}")
        print(f"  Tipo: {event.data.get('analysis_type')}")
        # Seria possível fazer coisas como notificar, salvar em banco, etc.
        event.add_result({"status": "processed"})
    return event.get_results()


@on_analysis_complete("repository")
async def notify_repository_analysis(target, analysis_name, result, **kwargs):
    """Handler para quando a análise de repositório for concluída."""
    print(f"\n📊 Relatório de análise de repositório concluído: {analysis_name}")
    if hasattr(result, "architecture"):
        print(f"  Arquitetura identificada: {result.architecture[:150]}...")
    # Em um cenário real: notificar equipe, integrar com CI/CD, etc.


# Demonstração do uso de Enhancers para potencializar análises
async def demonstrate_enhancers():
    """Demonstrar como os enhancers podem potencializar análises."""
    print("\nAnálise com Enhancers (Potencializadores)")
    print("=" * 50)

    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    repo = GitRepository(url=repo_url)

    # Análise regular para comparação
    print("\nExecutando análise regular (sem enhancers):")
    regular_analysis = await repo.analyze([AnalysisType.ARCHITECTURE])

    # Extrair apenas uma parte do resultado para exibição
    if hasattr(regular_analysis, "architecture"):
        regular_arch = regular_analysis.architecture[:200]
        print(f"\nResultado regular: {regular_arch}...")

    # 1. Análise com Deep Context Enhancer
    print("\nAnálise com Deep Context Enhancer (profundidade 4):")
    deep_context_result = await repo.with_enhancers([
        enhancer.deep_context(depth=4, include_history=True)
    ]).analyze([AnalysisType.ARCHITECTURE])

    if hasattr(deep_context_result, "architecture"):
        deep_context_arch = deep_context_result.architecture[:200]
        print(f"\nResultado com contexto profundo: {deep_context_arch}...")

        # Verificar metadados
        if hasattr(deep_context_result, "_metadata"):
            print(f"\nMetadados: {deep_context_result._metadata}")

    # 2. Análise com Best Practices Enhancer (focado em um framework)
    print("\nAnálise com Best Practices Enhancer (framework=Python):")
    best_practices_result = await repo.with_enhancers([
        enhancer.best_practices(
            framework="Python",
            patterns=["Factory", "Singleton", "Observer"],
            strictness="high",
        )
    ]).analyze([AnalysisType.PATTERNS])

    if hasattr(best_practices_result, "patterns"):
        patterns_result = best_practices_result.patterns
        print(f"\nPadrões identificados: {patterns_result}")

    # 3. Análise com Security Enhancer
    print("\nAnálise com Security Enhancer:")
    security_result = await repo.with_enhancers([
        enhancer.security(
            vulnerabilities=True,
            compliance=["OWASP Top 10", "PCI-DSS"],
            sensitive_data=True,
        )
    ]).analyze([AnalysisType.SECURITY])

    if hasattr(security_result, "security"):
        security_data = security_result.security
        risk_level = security_data.get("risk_level", "unknown")
        issues_count = security_data.get("count", 0)
        print(f"\nNível de risco: {risk_level}")
        print(f"Problemas de segurança encontrados: {issues_count}")

        # Verificar se há verificações de conformidade
        if "compliance_checks" in security_data:
            print("\nVerificações de conformidade:")
            for check in security_data["compliance_checks"]:
                print(f"  {check['standard']}: {check['status']}")

    # 4. Combinando múltiplos enhancers para uma análise abrangente
    print("\nCombinando múltiplos enhancers:")
    combined_result = await repo.with_enhancers([
        enhancer.deep_context(depth=3),
        enhancer.best_practices(framework="Python"),
        enhancer.performance(hotspots=True),
        enhancer.historical_trends(timespan="3m"),
    ]).analyze([AnalysisType.ARCHITECTURE, AnalysisType.COMPLEXITY])

    # Verificar resultados
    if hasattr(combined_result, "architecture"):
        combined_arch = combined_result.architecture[:200]
        print(f"\nArquitetura com enhancers combinados: {combined_arch}...")

    if hasattr(combined_result, "complexity"):
        complexity_data = combined_result.complexity

        # Verificar se há hotspots identificados
        if "metrics" in complexity_data and "hotspots" in complexity_data["metrics"]:
            hotspots = complexity_data["metrics"]["hotspots"]
            print(f"\nHotspots de complexidade: {hotspots}")

    # Comparar os diferentes resultados
    print("\nComparação do tamanho das análises:")
    regular_size = (
        len(regular_analysis.architecture)
        if hasattr(regular_analysis, "architecture")
        else 0
    )
    enhanced_size = (
        len(deep_context_result.architecture)
        if hasattr(deep_context_result, "architecture")
        else 0
    )
    combined_size = (
        len(combined_result.architecture)
        if hasattr(combined_result, "architecture")
        else 0
    )

    print(f"  Regular: {regular_size} caracteres")
    print(f"  Deep Context: {enhanced_size} caracteres")
    print(f"  Combinados: {combined_size} caracteres")


# Demonstração da funcionalidade de perguntas customizadas com enhancers
async def demonstrate_enhanced_questions():
    """Demonstrar como fazer perguntas potencializadas por enhancers."""
    print("\nPerguntas Potencializadas por Enhancers")
    print("=" * 50)

    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    repo = GitRepository(url=repo_url)

    # Assegurar que o repositório está clonado antes de prosseguir
    await repo.ensure_cloned()

    # Pergunta simples para comparação
    print("\nPergunta regular:")
    agent = await repo.get_agent()
    regular_answer = await agent.ask(
        "Como esta biblioteca poderia ser melhorada?", repo_url=repo.url
    )
    print(f"\nResposta regular: {regular_answer[:200]}...")

    # Pergunta com contexto profundo
    print("\nPergunta com contexto profundo:")
    deep_context = enhancer.deep_context(depth=5)
    context = deep_context.apply_to_context({})
    prompt = deep_context.enhance_prompt("Como esta biblioteca poderia ser melhorada?")

    deep_question = await agent.ask(prompt, repo_url=repo.url, **context)
    deep_question = deep_context.enhance_result(deep_question)
    print(f"\nResposta com contexto profundo: {deep_question[:200]}...")

    # Pergunta focada em melhores práticas
    print("\nPergunta com foco em melhores práticas:")
    bp_enhancer = enhancer.best_practices(framework="Python")
    context = bp_enhancer.apply_to_context({})
    prompt = bp_enhancer.enhance_prompt(
        "Quais padrões de design estão faltando neste código?"
    )

    best_practices_question = await agent.ask(prompt, repo_url=repo.url, **context)
    best_practices_question = bp_enhancer.enhance_result(best_practices_question)
    print(
        f"\nResposta com foco em melhores práticas: {best_practices_question[:200]}..."
    )

    # Pergunta sobre segurança
    print("\nPergunta com foco em segurança:")
    sec_enhancer = enhancer.security(compliance=["OWASP Top 10"])
    context = sec_enhancer.apply_to_context({})
    prompt = sec_enhancer.enhance_prompt(
        "Quais são os possíveis problemas de segurança neste código?"
    )

    security_question = await agent.ask(prompt, repo_url=repo.url, **context)
    security_question = sec_enhancer.enhance_result(security_question)
    print(f"\nResposta com foco em segurança: {security_question[:200]}...")

    # Pergunta com enhancers combinados
    print("\nPergunta com enhancers combinados:")
    enhancers_list = [
        enhancer.deep_context(depth=4),
        enhancer.historical_trends(),
        enhancer.performance(),
    ]

    context = {}
    prompt = "Como melhorar a arquitetura deste projeto para maior escalabilidade?"

    # Aplicar cada enhancer ao contexto e prompt
    for e in enhancers_list:
        context = e.apply_to_context(context)
        prompt = e.enhance_prompt(prompt)

    combined_question = await agent.ask(prompt, repo_url=repo.url, **context)

    # Aplicar enhancers ao resultado
    for e in enhancers_list:
        combined_question = e.enhance_result(combined_question)

    print(f"\nResposta com enhancers combinados: {combined_question[:200]}...")


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


async def main():
    """Executar o exemplo de enhancers."""
    print("\n===== ENHANCERS DO PEPPERPY =====")
    print("Demonstração das capacidades de potencialização de análises")

    # Demonstrar enhancers básicos
    try:
        await demonstrate_enhancers()
        print("\nDemonstração de enhancers concluída!")
    except Exception as e:
        print(f"Erro na demonstração de enhancers: {e}")

    # Demonstrar perguntas potencializadas
    try:
        await demonstrate_enhanced_questions()
        print("\nDemonstração de perguntas potencializadas concluída!")
    except Exception as e:
        print(f"Erro na demonstração de perguntas potencializadas: {e}")

    # Demonstrar enhancers customizados
    try:
        await demonstrate_custom_enhancer()
        print("\nDemonstração de enhancers customizados concluída!")
    except Exception as e:
        print(f"Erro na demonstração de enhancers customizados: {e}")

    print("\nExemplo de enhancers concluído!")


if __name__ == "__main__":
    asyncio.run(main())
