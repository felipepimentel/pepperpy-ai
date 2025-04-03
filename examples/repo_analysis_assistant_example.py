#!/usr/bin/env python3
"""Exemplo de análise de repositórios com PepperPy.

Este exemplo demonstra como usar a API declarativa do PepperPy
para analisar repositórios GitHub e responder perguntas sobre eles.
Utiliza os novos decoradores Domain-Specific Language (DSL) e handlers.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import (
    AnalysisLevel,
    AnalysisScope,
    AnalysisType,
    Repository,
    analyze,
    code_analysis,
    event_handler,
    on_analysis_complete,
    repository_task,
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


# Versão com decoradores DSL avançados
@repository_task(
    capabilities=["code_analysis", "repository_navigation"],
    scope=AnalysisScope.REPOSITORY,
    level=AnalysisLevel.DETAILED,
)
async def analyze_repo_architecture(repo):
    """Analisar a arquitetura do repositório."""
    print("Análise de Arquitetura de Repositório")
    print("=" * 50)

    # Definir repositório a ser analisado
    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"

    if isinstance(repo, str):
        # Se passamos a URL em vez do objeto repo
        repo = Repository(repo_url)

    # Criar tarefas específicas de análise
    @code_analysis(language="python")
    async def analyze_code_organization(repo):
        """Analisar organização do código e padrões."""
        return await repo.ask(
            "Analise a organização do código e identifique padrões arquiteturais"
        )

    @code_analysis(metrics=["complexity", "maintainability"])
    async def assess_code_quality(repo):
        """Avaliar qualidade do código."""
        return await repo.ask(
            "Avalie a qualidade do código quanto à complexidade e manutenibilidade"
        )

    # Executar análises customizadas
    print("\nExecutando análises específicas:")

    org_analysis = await analyze_code_organization(repo)
    print(f"\nOrganização do código: {org_analysis[:200]}...")

    quality_assessment = await assess_code_quality(repo)
    print(f"\nAvaliação de qualidade: {quality_assessment[:200]}...")

    # Usar nova API fluida para filtrar e analisar arquivos específicos
    python_files_analysis = (
        await repo.code_files().by_language("python").excluding("tests/*").analyze()
    )
    print(f"\nArquivos Python encontrados: {python_files_analysis.file_count}")

    # Gerar relatório com tipos específicos de análise
    analysis = await repo.analyze(
        analyses=[
            AnalysisType.ARCHITECTURE,
            AnalysisType.PATTERNS,
            AnalysisType.COMPLEXITY,
        ]
    )

    # Gerar relatório completo
    report = await analysis.generate_report()

    # Salvar resultado
    report_path = OUTPUT_DIR / "architectural_analysis_report.md"
    await report.save(report_path, format="md")
    print(f"\nRelatório detalhado salvo em: {report_path}")

    # Analisar mudanças desde um commit (exemplo)
    try:
        changes = await repo.changes_since("main")
        print(
            f"\nMudanças detectadas: {changes.commit_count if hasattr(changes, 'commit_count') else 'N/A'}"
        )
    except Exception as e:
        print(f"Erro ao analisar mudanças: {e}")

    # Sugerir padrões de design
    patterns = await repo.suggest_design_patterns()
    print(
        f"\nPadrões sugeridos: {patterns.suggestions[:150] if hasattr(patterns, 'suggestions') else 'N/A'}..."
    )

    return {
        "architecture_analysis": org_analysis,
        "quality_assessment": quality_assessment,
        "suggested_patterns": patterns.suggestions
        if hasattr(patterns, "suggestions")
        else None,
    }


# Versão ultra-simplificada ainda disponível
async def analyze_repo_simple():
    """Analisar um repositório com abordagem ultra-simplificada."""
    print("\nAnálise de Repositório - Abordagem Ultra-Simplificada")
    print("=" * 50)

    # Usar a função analyze diretamente - ela cuida de tudo
    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    result = await analyze(
        repo_url,
        objectives=["understand_purpose", "identify_structure", "summarize_code"],
    )

    # Acessar resultados
    print(f"\nPropósito: {result.purpose if hasattr(result, 'purpose') else 'N/A'}")
    print(
        f"\nEstrutura: {result.architecture if hasattr(result, 'architecture') else 'N/A'}"
    )

    # Salvar resultados
    report_path = OUTPUT_DIR / "repo_analysis_simple.md"
    await result.export(path=report_path, format="md")
    print(f"\nRelatório salvo em: {report_path}")

    return result


# Demonstração da API fluida de navegação de repositórios
async def demonstrate_repository_navigation():
    """Demonstrar capacidades avançadas de navegação em repositórios."""
    print("\nNavegação Avançada em Repositórios")
    print("=" * 50)

    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"

    async with Repository(repo_url) as repo:
        # Descobrir e listar branches
        branches = repo._branches
        print(
            f"\nBranches disponíveis: {', '.join(branches[:5] if len(branches) > 5 else branches)}"
        )

        # Contar arquivos por linguagem
        py_count = await repo.code_files().by_language("python").count()
        js_count = await repo.code_files().by_language("javascript").count()
        ts_count = await repo.code_files().by_language("typescript").count()

        print("\nArquivos por linguagem:")
        print(f"  Python: {py_count}")
        print(f"  JavaScript: {js_count}")
        print(f"  TypeScript: {ts_count}")

        # Análise de arquivos específicos
        main_files = await repo.code_files().matching("**/main.py").analyze()
        if hasattr(main_files, "file_count") and main_files.file_count > 0:
            print(f"\nArquivos main.py encontrados: {main_files.file_count}")
            print(
                f"Análise: {main_files.analysis[:150] if hasattr(main_files, 'analysis') else 'N/A'}..."
            )
        else:
            print("\nNenhum arquivo main.py encontrado")


async def main():
    """Executar o exemplo de análise de repositório."""
    # Executar versão com decoradores DSL
    try:
        repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
        result_decorator = await analyze_repo_architecture(repo_url)
        print("\nAnálise com decoradores DSL concluída!")
    except Exception as e:
        print(f"Erro na análise com decorador DSL: {e}")

    # Executar versão simplificada
    try:
        result_simple = await analyze_repo_simple()
        print("\nAnálise simplificada concluída!")
    except Exception as e:
        print(f"Erro na análise simplificada: {e}")

    # Demonstrar navegação avançada
    try:
        await demonstrate_repository_navigation()
        print("\nDemonstração de navegação concluída!")
    except Exception as e:
        print(f"Erro na demonstração de navegação: {e}")

    print("\nExemplo de análise de repositório concluído!")


if __name__ == "__main__":
    asyncio.run(main())
