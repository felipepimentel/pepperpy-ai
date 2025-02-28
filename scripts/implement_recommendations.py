#!/usr/bin/env python
"""
Script para implementar todas as recomendações de reestruturação do PepperPy.
Este script executa as seguintes alterações:
1. Padronização de idioma
2. Consolidação de sistemas de erro
3. Unificação de provedores
4. Reorganização de módulos
5. Remoção de redundâncias
6. Definição de fronteiras claras entre common e core
7. Unificação de sistemas de plugins
8. Consolidação do sistema de cache
"""

import os
import shutil
import sys
from pathlib import Path

# Adicionar o diretório pai ao caminho para importar o restructure.py
sys.path.append(str(Path(__file__).parent))
from restructure import (
    PEPPERPY_DIR,
    create_init_file,
    create_reexport_stub,
    ensure_directory_exists,
    move_module,
    update_imports_in_project,
)


def standardize_language():
    """
    1. Padronização de idioma - traduz todas as descrições em português para inglês.
    """
    print("1. Padronizando idioma...")

    # Dicionário de tradução - adicione mais conforme necessário
    translation_dict = {
        # Traduções gerais
        "Adaptadores para integração com frameworks e bibliotecas de terceiros": "Adapters for integration with third-party frameworks and libraries",
        "Capacidades cognitivas implementadas pelos agentes": "Cognitive capabilities implemented by agents",
        "Tipos específicos de agentes implementados pelo framework": "Specific agent types implemented by the framework",
        "Componentes principais do sistema de workflows": "Main components of the workflow system",
        "Definição e construção de workflows": "Workflow definition and construction",
        "Execução e controle de workflows": "Workflow execution and control",
        "Utilitários para manipulação de dados": "Utilities for data manipulation",
        "Utilitários para manipulação de datas": "Utilities for date manipulation",
        "Utilitários para manipulação de arquivos": "Utilities for file manipulation",
        "Utilitários para manipulação de números": "Utilities for number manipulation",
        "Framework modular para construção de aplicações baseadas em IA": "Modular framework for building AI-based applications",
    }

    # Percorre todos os arquivos __init__.py e atualiza as descrições
    for root, _, files in os.walk(PEPPERPY_DIR):
        for file in files:
            if file == "__init__.py":
                file_path = Path(root) / file
                with open(file_path, "r") as f:
                    content = f.read()

                # Procura por docstrings em português e traduz
                for pt, en in translation_dict.items():
                    if pt in content:
                        content = content.replace(pt, en)

                with open(file_path, "w") as f:
                    f.write(content)


def consolidate_error_systems():
    """
    2. Consolidação de sistemas de erro - unifica os sistemas de erro duplicados.
    """
    print("2. Consolidando sistemas de erro...")

    # Diretório de origem (sistema duplicado) e destino (sistema consolidado)
    common_errors = PEPPERPY_DIR / "common" / "errors"
    core_errors = PEPPERPY_DIR / "core" / "errors"

    # Verifica se os diretórios existem
    if not common_errors.exists() or not core_errors.exists():
        print("Aviso: Diretórios de erro não encontrados")
        return

    # Move todos os arquivos e subdiretórios de common/errors para core/errors
    for item in common_errors.iterdir():
        dest_item = core_errors / item.name
        if not dest_item.exists():
            if item.is_file():
                shutil.copy2(item, dest_item)
            elif item.is_dir():
                move_module(item, dest_item)

    # Cria um stub de compatibilidade em common/errors
    create_reexport_stub(common_errors, core_errors)

    # Atualiza imports no projeto
    import_mappings = {"pepperpy.common.errors": "pepperpy.core.errors"}
    update_imports_in_project(import_mappings)


def unify_provider_system():
    """
    3. Unificação de provedores - centraliza os provedores em um único local.
    """
    print("3. Unificando sistema de provedores...")

    # Cria diretório central de provedores
    providers_dir = PEPPERPY_DIR / "providers"
    ensure_directory_exists(providers_dir)
    create_init_file(providers_dir, "Unified provider system for PepperPy")

    # Mapeia diretórios de provedores para mover
    provider_locations = [
        ("agents/providers", "agent"),
        ("audio/providers", "audio"),
        ("vision/providers", "vision"),
        ("llm/providers", "llm"),
        ("rag/providers", "rag"),
        ("cloud/providers", "cloud"),
        ("core/config/providers", "config"),
    ]

    # Mapeamento de imports para atualizar
    import_mappings = {}

    # Move cada diretório de provedor para o local centralizado
    for rel_path, provider_type in provider_locations:
        source = PEPPERPY_DIR / rel_path
        if not source.exists():
            print(f"Aviso: Diretório de provedor não encontrado: {source}")
            continue

        # Cria diretório de destino para este tipo de provedor
        dest = providers_dir / provider_type
        ensure_directory_exists(dest)
        create_init_file(
            dest, f"Provider implementations for {provider_type} capabilities"
        )

        # Move arquivos e subdiretórios
        for item in source.iterdir():
            if item.name != "__init__.py":  # Ignora o __init__.py original
                dest_item = dest / item.name
                if item.is_file():
                    shutil.copy2(item, dest_item)
                elif item.is_dir():
                    move_module(item, dest_item)

        # Cria stub de compatibilidade
        create_reexport_stub(source, dest)

        # Adiciona ao mapeamento de imports
        old_import = f"pepperpy.{rel_path.replace('/', '.')}"
        new_import = f"pepperpy.providers.{provider_type}"
        import_mappings[old_import] = new_import

    # Atualiza imports
    update_imports_in_project(import_mappings)


def reorganize_workflows():
    """
    4. Reorganização de workflows - move workflows de agents para um módulo de alto nível.
    """
    print("4. Reorganizando módulo de workflows...")

    # Origem e destino dos workflows
    source = PEPPERPY_DIR / "agents" / "workflows"
    destination = PEPPERPY_DIR / "workflows"

    if not source.exists():
        print("Aviso: Diretório de workflows não encontrado")
        return

    # Move o módulo de workflows
    move_module(source, destination)

    # Cria stub de compatibilidade
    create_reexport_stub(source, destination)

    # Atualiza imports
    import_mappings = {"pepperpy.agents.workflows": "pepperpy.workflows"}
    update_imports_in_project(import_mappings)


def consolidate_implementations():
    """
    5. Consolidação de implementações - remove arquivos redundantes.
    """
    print("5. Consolidando implementações redundantes...")

    # Lista de arquivos de implementação e diretórios correspondentes
    redundant_pairs = [
        ("agents/implementations.py", "agents/implementations"),
        ("core/implementations.py", "core/implementations"),
        ("rag/implementations.py", "rag/implementations"),
    ]

    for file_path, dir_path in redundant_pairs:
        file_full_path = PEPPERPY_DIR / file_path
        dir_full_path = PEPPERPY_DIR / dir_path

        if file_full_path.exists() and dir_full_path.exists():
            # Verifica se há classes ou funções no arquivo que não estão no diretório
            # Se houver, move-as para arquivos apropriados no diretório

            # Para este exemplo, simplesmente movemos o conteúdo do arquivo para um novo arquivo no diretório
            implementations_content = ""
            if file_full_path.exists():
                with open(file_full_path, "r") as f:
                    implementations_content = f.read()

            if implementations_content:
                # Cria um arquivo consolidated.py no diretório para o conteúdo do arquivo original
                with open(dir_full_path / "consolidated.py", "w") as f:
                    f.write('"""Consolidated implementations"""\n\n')
                    f.write(implementations_content)

            # Cria o stub de compatibilidade
            if file_full_path.exists():
                create_reexport_stub(file_full_path, dir_full_path)


def define_common_core_boundaries():
    """
    6. Definição de fronteiras entre common e core - reorganiza os módulos.
    """
    print("6. Definindo fronteiras entre common e core...")

    # Lista de itens a mover de common para core
    common_to_core = [
        ("common/types", "core/types"),
    ]

    # Lista de itens a mover de core para common
    core_to_common = [
        ("core/utils", "common/utils"),
    ]

    # Processa movimentações common -> core
    import_mappings = {}
    for source_rel, dest_rel in common_to_core:
        source = PEPPERPY_DIR / source_rel
        dest = PEPPERPY_DIR / dest_rel

        if source.exists():
            # Move o módulo
            move_module(source, dest)

            # Cria stub de compatibilidade
            create_reexport_stub(source, dest)

            # Adiciona ao mapeamento de imports
            old_import = f"pepperpy.{source_rel.replace('/', '.')}"
            new_import = f"pepperpy.{dest_rel.replace('/', '.')}"
            import_mappings[old_import] = new_import

    # Processa movimentações core -> common
    for source_rel, dest_rel in core_to_common:
        source = PEPPERPY_DIR / source_rel
        dest = PEPPERPY_DIR / dest_rel

        if source.exists():
            # Move o módulo
            move_module(source, dest)

            # Cria stub de compatibilidade
            create_reexport_stub(source, dest)

            # Adiciona ao mapeamento de imports
            old_import = f"pepperpy.{source_rel.replace('/', '.')}"
            new_import = f"pepperpy.{dest_rel.replace('/', '.')}"
            import_mappings[old_import] = new_import

    # Atualiza imports
    update_imports_in_project(import_mappings)


def unify_plugin_systems():
    """
    7. Unificação de sistemas de plugins - integra os plugins da CLI com o sistema principal.
    """
    print("7. Unificando sistemas de plugins...")

    # Origem e destino dos plugins da CLI
    cli_plugins = PEPPERPY_DIR / "cli" / "plugins"
    core_plugins = PEPPERPY_DIR / "core" / "plugins"

    if not cli_plugins.exists() or not core_plugins.exists():
        print("Aviso: Diretórios de plugins não encontrados")
        return

    # Cria um novo diretório de plugins para a CLI no sistema principal
    cli_plugins_dest = core_plugins / "cli"
    ensure_directory_exists(cli_plugins_dest)
    create_init_file(
        cli_plugins_dest, "CLI plugin system integrated with the core plugin system"
    )

    # Move os plugins da CLI
    for item in cli_plugins.iterdir():
        if item.name != "__init__.py":  # Ignora o __init__.py original
            dest_item = cli_plugins_dest / item.name
            if item.is_file():
                shutil.copy2(item, dest_item)
            elif item.is_dir():
                move_module(item, dest_item)

    # Cria stub de compatibilidade
    create_reexport_stub(cli_plugins, cli_plugins_dest)

    # Atualiza imports
    import_mappings = {"pepperpy.cli.plugins": "pepperpy.core.plugins.cli"}
    update_imports_in_project(import_mappings)


def consolidate_caching_system():
    """
    8. Consolidação do sistema de cache - unifica as implementações redundantes.
    """
    print("8. Consolidando sistema de cache...")

    # Diretório de cache
    caching_dir = PEPPERPY_DIR / "caching"

    if not caching_dir.exists():
        print("Aviso: Diretório de cache não encontrado")
        return

    # Lista de arquivos redundantes e seus destinos consolidados
    redundant_cache_files = [
        ("memory.py", "memory_cache.py", "memory.py"),  # (arquivo1, arquivo2, destino)
    ]

    for file1, file2, dest in redundant_cache_files:
        file1_path = caching_dir / file1
        file2_path = caching_dir / file2
        dest_path = caching_dir / dest

        if file1_path.exists() and file2_path.exists():
            # Lê o conteúdo dos dois arquivos
            with open(file1_path, "r") as f:
                content1 = f.read()

            with open(file2_path, "r") as f:
                content2 = f.read()

            # Consolida o conteúdo - neste caso simplificado, mantemos o primeiro arquivo
            # e criamos um stub no segundo arquivo
            with open(dest_path, "w") as f:
                f.write(content1)

            # Cria stub de compatibilidade no segundo arquivo
            create_reexport_stub(file2_path, dest_path)


def standardize_module_organization():
    """
    9. Padronização da organização de módulos - reorganiza por domínio em vez de tipo técnico.
    """
    print("9. Padronizando organização de módulos...")

    # Reorganiza módulos específicos para seguir a organização por domínio
    # Esta é uma tarefa mais complexa que dependeria de uma análise detalhada
    # de cada módulo, por isso estamos apenas preparando a estrutura inicial

    # Cria um diretório capabilities para organizar as capacidades
    capabilities_dir = PEPPERPY_DIR / "capabilities"
    ensure_directory_exists(capabilities_dir)
    create_init_file(
        capabilities_dir, "Domain-specific capabilities of the PepperPy framework"
    )

    # Move os módulos de capacidades técnicas para o novo diretório
    capability_modules = [
        ("audio", "audio"),
        ("vision", "vision"),
        ("multimodal", "multimodal"),
    ]

    import_mappings = {}

    for module_name, capability_name in capability_modules:
        source = PEPPERPY_DIR / module_name
        dest = capabilities_dir / capability_name

        if source.exists():
            # Move o módulo
            move_module(source, dest)

            # Cria stub de compatibilidade
            create_reexport_stub(source, dest)

            # Adiciona ao mapeamento de imports
            old_import = f"pepperpy.{module_name}"
            new_import = f"pepperpy.capabilities.{capability_name}"
            import_mappings[old_import] = new_import

    # Atualiza imports
    update_imports_in_project(import_mappings)


def main():
    """Executa todas as etapas de reestruturação."""
    print("Implementando recomendações para a estrutura do PepperPy...")

    # Sequência recomendada para implementação
    standardize_language()
    consolidate_error_systems()
    unify_provider_system()
    reorganize_workflows()
    consolidate_implementations()
    define_common_core_boundaries()
    unify_plugin_systems()
    consolidate_caching_system()
    standardize_module_organization()

    print("Reestruturação concluída!")


if __name__ == "__main__":
    main()
