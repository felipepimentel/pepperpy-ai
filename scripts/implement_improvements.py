#!/usr/bin/env python3
"""
Script para implementar melhorias adicionais na estrutura do projeto PepperPy.

Este script coordena a implementação das seguintes melhorias:
1. Centralização de Configuração
2. Otimização de Dependências
3. Interface Pública vs. Implementação Interna
4. Padronização de Documentação
5. Consolidação de Utilitários
6. Sistema de Plugins Mais Robusto
"""

import argparse
import sys
from pathlib import Path

# Adiciona o diretório do script ao PATH para permitir importações relativas
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Importa os módulos de melhoria
from improvements.centralize_config import implement_config_centralization
from improvements.consolidate_utils import implement_utils_consolidation
from improvements.create_interfaces import implement_public_interfaces
from improvements.enhance_plugins import implement_plugin_system
from improvements.optimize_dependencies import implement_dependency_optimization
from improvements.standardize_docs import implement_documentation_standards


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Implementar melhorias adicionais na estrutura do projeto PepperPy."
    )
    parser.add_argument(
        "--all", action="store_true", help="Implementar todas as melhorias"
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Implementar centralização de configuração",
    )
    parser.add_argument(
        "--deps", action="store_true", help="Implementar otimização de dependências"
    )
    parser.add_argument(
        "--interfaces", action="store_true", help="Implementar interfaces públicas"
    )
    parser.add_argument(
        "--docs", action="store_true", help="Implementar padrões de documentação"
    )
    parser.add_argument(
        "--utils", action="store_true", help="Implementar consolidação de utilitários"
    )
    parser.add_argument(
        "--plugins",
        action="store_true",
        help="Implementar sistema de plugins melhorado",
    )

    return parser.parse_args()


def create_backup(module_name):
    """Cria um backup antes de modificar um módulo."""
    backup_dir = Path("backup") / "improvements" / module_name
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def main():
    """Função principal para executar as melhorias."""
    args = parse_args()
    project_root = Path(__file__).parent.parent

    # Verifica se alguma flag específica foi passada
    specific_flags = (
        args.config
        or args.deps
        or args.interfaces
        or args.docs
        or args.utils
        or args.plugins
    )

    # Se nenhuma flag específica foi passada e --all não foi especificado, mostrar ajuda
    if not specific_flags and not args.all:
        print(
            "Erro: Nenhuma melhoria selecionada. Use --all ou especifique melhorias individuais."
        )
        print(
            "Execute 'python scripts/implement_improvements.py --help' para ver as opções disponíveis."
        )
        return 1

    # Determina quais melhorias implementar
    implement_config = args.all or args.config
    implement_deps = args.all or args.deps
    implement_interfaces = args.all or args.interfaces
    implement_docs = args.all or args.docs
    implement_utils = args.all or args.utils
    implement_plugins = args.all or args.plugins

    print("=" * 80)
    print("IMPLEMENTAÇÃO DE MELHORIAS NA ESTRUTURA DO PROJETO PEPPERPY")
    print("=" * 80)

    # 1. Centralização de Configuração
    if implement_config:
        print("\n[1/6] Implementando centralização de configuração...")
        config_backup = create_backup("config")
        implement_config_centralization(project_root, config_backup)

    # 2. Otimização de Dependências
    if implement_deps:
        print("\n[2/6] Implementando otimização de dependências...")
        deps_backup = create_backup("dependencies")
        implement_dependency_optimization(project_root, deps_backup)

    # 3. Interface Pública vs. Implementação Interna
    if implement_interfaces:
        print("\n[3/6] Implementando interfaces públicas...")
        interfaces_backup = create_backup("interfaces")
        implement_public_interfaces(project_root, interfaces_backup)

    # 4. Padronização de Documentação
    if implement_docs:
        print("\n[4/6] Implementando padrões de documentação...")
        docs_backup = create_backup("documentation")
        implement_documentation_standards(project_root, docs_backup)

    # 5. Consolidação de Utilitários
    if implement_utils:
        print("\n[5/6] Implementando consolidação de utilitários...")
        utils_backup = create_backup("utils")
        implement_utils_consolidation(project_root, utils_backup)

    # 6. Sistema de Plugins Mais Robusto
    if implement_plugins:
        print("\n[6/6] Implementando sistema de plugins melhorado...")
        plugins_backup = create_backup("plugins")
        implement_plugin_system(project_root, plugins_backup)

    print("\n" + "=" * 80)
    print("IMPLEMENTAÇÃO DE MELHORIAS CONCLUÍDA")
    print("=" * 80)
    print(
        "\nExecute 'python scripts/validate_improvements.py' para validar as melhorias implementadas."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
